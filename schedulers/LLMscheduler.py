import unsloth
import torch
import time
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from models import Machine, Carrier, Shelf, StandardResponse
from models.exceptions import (
    ErrorStructure,
    NonExistentMachine,
    NonExistentCarrier,
    FaultOrigin,
    FaultDestination,
    FaultCarrier,
    FullDestination
)
from unsloth.models import FastModel
from utils.greedy import RandomGreddy
from utils.promptConvert import json_to_prompt
import orjson as json
import re

class QwenLoraPredictor:
    def __init__(self, base_model_path: str, adapter_path: str):
        """
        初始化模型和 tokenizer
        """
        self.tokenizer = AutoTokenizer.from_pretrained(
            base_model_path, trust_remote_code=True, local_files_only=True
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            base_model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
            local_files_only=True
        )
        
        self.machines: dict[str, Machine] = {}
        self.carriers: dict[str, Carrier] = {}
        self.shelves: dict[str, Shelf] = {}
        
        self.model = PeftModel.from_pretrained(
            self.model,
            adapter_path,
            local_files_only=True
        )
        self.model.eval()

    def predict(self, instruction: str, input_text: str, max_new_tokens: int = 64) -> str:
        """
        根据 instruction 和 input_text 返回 assistant 的输出，并记录首字延迟和总输出时间
        """
        prompt = (
            f"<|im_start|>system\n现在你是一名工厂调度师。<|im_end|>\n"
            f"<|im_start|>user\n{instruction + input_text}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )

        # 构造输入
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)        

        # 推理
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                top_p=0.9,
                temperature=0.8,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                output_scores=True,
                return_dict_in_generate=True
            )

        # 提取生成内容
        generated_ids = outputs.sequences[0]
        decoded = self.tokenizer.decode(generated_ids, skip_special_tokens=False)

        # 提取 assistant 输出
        return decoded.split("<|im_start|>assistant\n")[-1].split("<|im_end|>")[0].strip()
    
    def __call__(self, machines: dict[str, Machine], shelves: dict[str, Shelf], carriers: dict[str, Carrier]) -> tuple[StandardResponse, dict[str, float]]:
        self.machines = machines
        self.shelves = shelves
        self.carriers = carriers
        state = {
            "machines": [machine.model_dump() for machine in machines.values()],
            "shelves": [shelf.model_dump() for shelf in shelves.values()],
            "carriers": [carrier.model_dump() for carrier in carriers.values()]
        }
        try:
            # 推理开始时间
            total_start = time.time()
            result = self.predict(
                instruction="根据当前工厂生产情况规划下一步行动",
                input_text=json_to_prompt(state),
                # max_new_tokens=2048
            )
            total_end = time.time()
            print(f"[LOG] Total generation time: {total_end - total_start:.3f} 秒")
            result = json.loads(result)
        except json.JSONDecodeError as e:
            raise ErrorStructure() from e
        except Exception as e:
            print(f"Error: {e}")
            raise e
        carrier = result["carrier"]
        orgi = result["orgi"]
        dest = result["dest"]
        if carrier not in self.carriers.keys():
            raise NonExistentCarrier()
        if orgi not in shelves.keys() and orgi not in machines.keys():
            raise NonExistentMachine()
        if dest not in shelves.keys() and dest not in machines.keys():
            raise NonExistentMachine()
        if self.carriers[carrier].status != 1:
            raise FaultCarrier()
        if (
            dest in machines.keys() and 
            carriers[carrier].workflow[carriers[carrier].current][0] not in machines[dest].tags
        ):
            raise FaultDestination()
        if carriers[carrier].at != orgi:
            raise FaultOrigin()
        if dest in shelves.keys() and shelves[dest].free <= 0:
            raise FullDestination()
        if dest in machines.keys() and machines[dest].free <= 0:
            raise FullDestination()
        return result, {
            "predict_cost": total_end - total_start
        }
        
class QwenUnslothPredictor:
    def __init__(self, model_path: str):
        """
        初始化模型和 tokenizer
        """
        self.model, self.tokenizer = FastModel.from_pretrained(
            model_path,
            load_in_4bit=True,
            local_files_only=True
        )
        
        self.machines: dict[str, Machine] = {}
        self.carriers: dict[str, Carrier] = {}
        self.shelves: dict[str, Shelf] = {}
        
        FastModel.for_inference(self.model)

    def predict(self, instruction: str, input_text: str, max_new_tokens: int = 64) -> str:
        """
        根据 instruction 和 input_text 返回 assistant 的输出，并记录首字延迟和总输出时间
        """
        messages = [
            { "role": "system", "content": instruction },
            { "role": "user", "content": input_text },
        ]
        text = self.tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
        inputs = self.tokenizer(text, add_special_tokens=False, return_tensors="pt").to("cuda")
        # 推理
        with torch.inference_mode():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                top_p=0.95,
                temperature=0.6,
                pad_token_id=self.tokenizer.pad_token_id,
            )

        # 提取生成内容
        outputs = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        pattern = r'<think>(.*?)</think>'
        matches = re.findall(pattern, outputs, re.DOTALL)
        return matches, outputs.split("</think>")[-1].strip()
    
    def __call__(self, 
                 machines: dict[str, Machine], 
                 shelves: dict[str, Shelf], 
                 carriers: dict[str, Carrier], 
                 distance: dict[tuple[str, str], int]
    ) -> tuple[StandardResponse, dict[str, float]]:
        self.machines = machines
        self.shelves = shelves
        self.carriers = carriers
        state = {
            "machines": [machine.model_dump() for machine in machines.values()],
            "shelves": [shelf.model_dump() for shelf in shelves.values()],
            "carriers": [carrier.model_dump() for carrier in carriers.values()],
            "distance": distance
        }
        try:
            # 推理开始时间
            total_start = time.time()
            result = self.predict(
                instruction="根据当前工厂生产情况规划下一步行动",
                input_text=json_to_prompt(state),
                max_new_tokens=2048
            )
            total_end = time.time()
            print(f"[LOG] Total generation time: {total_end - total_start:.3f} 秒")
            think = result[0]
            result = json.loads(result[1])
            print(result)
        except json.JSONDecodeError as e:
            raise ErrorStructure() from e
        except Exception as e:
            print(f"Error: {e}")
            raise e
        carrier = result["carrier"]
        orgi = result["orgi"]
        dest = result["dest"]
        if carrier == "None" or carrier is None:
            result["carrier"] = None
            result["orgi"] = None
            result["dest"] = None
            return result, {
                "think": think,
                "predict_cost": total_end - total_start
            }
        if carrier not in self.carriers.keys():
            raise NonExistentCarrier()
        if orgi not in shelves.keys() and orgi not in machines.keys():
            raise NonExistentMachine()
        if dest not in shelves.keys() and dest not in machines.keys():
            raise NonExistentMachine()
        if self.carriers[carrier].status != 1:
            raise FaultCarrier()
        if (
            dest in machines.keys() and 
            carriers[carrier].workflow[carriers[carrier].current][0] not in machines[dest].tags
        ):
            raise FaultDestination()
        if carriers[carrier].at != orgi:
            raise FaultOrigin()
        if dest in shelves.keys() and shelves[dest].free <= 0:
            raise FullDestination()
        if dest in machines.keys() and machines[dest].free <= 0:
            raise FullDestination()
        return result, {
            "think": think,
            "predict_cost": total_end - total_start
        }