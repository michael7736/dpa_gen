"""
AI!�'�K�
K�!��͔��ό(�
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os
from dataclasses import dataclass, field
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import tiktoken
import matplotlib.pyplot as plt
import numpy as np

# K�Mn
MODEL_CONFIGS = {
    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-3.5-turbo"
        ]
    },
    "anthropic": {
        "api_key": os.getenv("ANTHROPIC_API_KEY"),
        "models": [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]
    },
    "deepseek": {
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
        "base_url": "https://api.deepseek.com/v1",
        "models": [
            "deepseek-chat"
        ]
    }
}

# K�(�
TEST_CASES = {
    "simple_qa": {
        "name": "�U�T",
        "prompt": "�H/:hf`�( �݀U��",
        "max_tokens": 100,
        "temperature": 0.7
    },
    "complex_reasoning": {
        "name": "B�",
        "prompt": """��:ov����
         �l�	100�� �(AI�/
Z	�
        ��;� B/1	�cz� 2	�7�� 3	pn�
        ����/	����!�	��@����Mn""",
        "max_tokens": 500,
        "temperature": 0.7
    },
    "code_generation": {
        "name": "�",
        "prompt": """� *Python�p�����
        1. �6 *�,h\:�e
        2. (TF-IDF���,�<�
        3. �� �<��,��v�<�p
        �B(scikit-learn�+�""",
        "max_tokens": 800,
        "temperature": 0.5
    },
    "summarization": {
        "name": "�,X�",
        "prompt": """�;��vѰ�8Á���3*��	
        
         �vh'�� !�(�,�X("-�W�"�a
        v�XǞ�ѰS�e�,���!�
���50%�
        !���,-���㌰���>WM�Ͱa(@	
        KՄ!�-�	��F�v�Ѱ�y���:
        ��/��s.�o�ӄ�e�����*�
        dv��� Ͱ��0e���W��""",
        "max_tokens": 200,
        "temperature": 0.5
    },
    "structured_extraction": {
        "name": "ӄ��",
        "prompt": """���,-��s.�o�JSON<��
        
         	735�o��(�р	Pl��\�8t
        ־PythonJava�Go� 	0̄����ό
         ��&���� *�;C��P��y�
        
         ����t�L�\tP��hy�ό""",
        "max_tokens": 300,
        "temperature": 0.3
    }
}


@dataclass
class ModelTestResult:
    """!�K�Ӝ"""
    provider: str
    model: str
    test_case: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    response_times: List[float] = field(default_factory=list)
    token_counts: List[int] = field(default_factory=list)
    costs: List[float] = field(default_factory=list)
    quality_scores: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def avg_response_time(self) -> float:
        return statistics.mean(self.response_times) if self.response_times else 0
    
    @property
    def avg_tokens(self) -> float:
        return statistics.mean(self.token_counts) if self.token_counts else 0
    
    @property
    def total_cost(self) -> float:
        return sum(self.costs)
    
    @property
    def success_rate(self) -> float:
        total = self.total_requests
        return self.successful_requests / total if total > 0 else 0
    
    @property
    def p95_response_time(self) -> float:
        if self.response_times:
            sorted_times = sorted(self.response_times)
            idx = int(len(sorted_times) * 0.95)
            return sorted_times[idx]
        return 0


class ModelPerformanceTester:
    """AI!�'�K�h"""
    
    def __init__(self):
        self.results: List[ModelTestResult] = []
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # ��7�
        self.clients = {
            "openai": AsyncOpenAI(api_key=MODEL_CONFIGS["openai"]["api_key"]),
            "anthropic": AsyncAnthropic(api_key=MODEL_CONFIGS["anthropic"]["api_key"]),
            "deepseek": AsyncOpenAI(
                api_key=MODEL_CONFIGS["deepseek"]["api_key"],
                base_url=MODEL_CONFIGS["deepseek"]["base_url"]
            )
        }
    
    async def test_all_models(self, test_iterations: int = 10):
        """K�@	!�"""
        print(" �AI!�'�K�")
        print("="*60)
        
        # OpenAI!�K�
        for model in MODEL_CONFIGS["openai"]["models"]:
            await self.test_model("openai", model, test_iterations)
        
        # Anthropic!�K�
        for model in MODEL_CONFIGS["anthropic"]["models"]:
            await self.test_model("anthropic", model, test_iterations)
        
        # DeepSeek!�K�
        for model in MODEL_CONFIGS["deepseek"]["models"]:
            await self.test_model("deepseek", model, test_iterations)
        
        # �J
        self.generate_report()
        self.plot_results()
    
    async def test_model(self, provider: str, model: str, iterations: int):
        """K�U*!�"""
        print(f"\nK� {provider} - {model}")
        print("-"*40)
        
        for test_name, test_config in TEST_CASES.items():
            print(f"\ngLK�: {test_config['name']}")
            
            result = ModelTestResult(
                provider=provider,
                model=model,
                test_case=test_name,
                total_requests=iterations,
                successful_requests=0,
                failed_requests=0
            )
            
            for i in range(iterations):
                try:
                    # gLK�
                    response_data = await self._call_model(
                        provider, model,
                        test_config["prompt"],
                        test_config["max_tokens"],
                        test_config["temperature"]
                    )
                    
                    if response_data:
                        result.successful_requests += 1
                        result.response_times.append(response_data["response_time"])
                        result.token_counts.append(response_data["total_tokens"])
                        result.costs.append(response_data["cost"])
                        
                        # �U�(����͔��/&+s.�	
                        quality = self._evaluate_quality(
                            test_config["prompt"],
                            response_data["content"],
                            test_name
                        )
                        result.quality_scores.append(quality)
                    else:
                        result.failed_requests += 1
                        
                except Exception as e:
                    result.failed_requests += 1
                    result.errors.append(str(e))
                    print(f"  �� {i+1} 1%: {e}")
                
                # >:ۦ
                if (i + 1) % 5 == 0:
                    print(f"  � {i+1}/{iterations} !K�")
            
            # SpӜX�
            self._print_test_summary(result)
            self.results.append(result)
    
    async def _call_model(
        self,
        provider: str,
        model: str,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Optional[Dict[str, Any]]:
        """(!�API"""
        start_time = time.time()
        
        try:
            if provider == "openai" or provider == "deepseek":
                client = self.clients[provider]
                response = await client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                content = response.choices[0].message.content
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
                total_tokens = response.usage.total_tokens
                
                # ��,���	
                cost = self._calculate_cost(
                    provider, model, prompt_tokens, completion_tokens
                )
                
            elif provider == "anthropic":
                client = self.clients[provider]
                response = await client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                content = response.content[0].text
                # Anthropic�token��
                prompt_tokens = len(self.tokenizer.encode(prompt))
                completion_tokens = len(self.tokenizer.encode(content))
                total_tokens = prompt_tokens + completion_tokens
                
                cost = self._calculate_cost(
                    provider, model, prompt_tokens, completion_tokens
                )
            
            response_time = time.time() - start_time
            
            return {
                "content": content,
                "response_time": response_time,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "cost": cost
            }
            
        except Exception as e:
            print(f"API(�: {e}")
            return None
    
    def _calculate_cost(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """��API(,�C	"""
        # ��,���E�<��	
        pricing = {
            "openai": {
                "gpt-4o": {"prompt": 0.01, "completion": 0.03},
                "gpt-4o-mini": {"prompt": 0.0001, "completion": 0.0002},
                "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015}
            },
            "anthropic": {
                "claude-3-opus-20240229": {"prompt": 0.015, "completion": 0.075},
                "claude-3-sonnet-20240229": {"prompt": 0.003, "completion": 0.015},
                "claude-3-haiku-20240307": {"prompt": 0.00025, "completion": 0.00125}
            },
            "deepseek": {
                "deepseek-chat": {"prompt": 0.0001, "completion": 0.0002}
            }
        }
        
        if provider in pricing and model in pricing[provider]:
            rates = pricing[provider][model]
            cost = (prompt_tokens * rates["prompt"] + 
                   completion_tokens * rates["completion"]) / 1000
            return cost
        
        return 0.0
    
    def _evaluate_quality(self, prompt: str, response: str, test_case: str) -> float:
        """�U�(��00-1	"""
        score = 0.0
        
        # �@͔:z
        if response and len(response) > 10:
            score += 0.3
        
        # �'
        if 50 < len(response) < 2000:
            score += 0.2
        
        # ��K�(��y��0
        if test_case == "simple_qa":
            if ":hf`" in response and len(response) < 200:
                score += 0.5
        elif test_case == "code_generation":
            if "def " in response and "import" in response:
                score += 0.5
        elif test_case == "structured_extraction":
            try:
                # ��JSON
                json.loads(response)
                score += 0.5
            except:
                pass
        else:
            # (�0��/&+s.�
            keywords = ["��", "�", ";�", "��"]
            if any(keyword in response for keyword in keywords):
                score += 0.5
        
        return min(score, 1.0)
    
    def _print_test_summary(self, result: ModelTestResult):
        """SpK�X�"""
        print(f"\n  K�Ӝ - {TEST_CASES[result.test_case]['name']}:")
        print(f"    ��: {result.success_rate:.1%}")
        print(f"    sG͔��: {result.avg_response_time:.2f}�")
        print(f"    P95͔��: {result.p95_response_time:.2f}�")
        print(f"    sGtokens: {result.avg_tokens:.0f}")
        print(f"    ;,: ${result.total_cost:.4f}")
        if result.quality_scores:
            print(f"    sG(�: {statistics.mean(result.quality_scores):.2f}")
    
    def generate_report(self, filename: str = "model_performance_report.md"):
        """'��J"""
        with open(filename, "w") as f:
            f.write("# AI!�'�KեJ\n\n")
            f.write(f"K���: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 	ЛF�
            provider_results = {}
            for result in self.results:
                key = f"{result.provider}-{result.model}"
                if key not in provider_results:
                    provider_results[key] = []
                provider_results[key].append(result)
            
            # X�h
            f.write("## '�X�\n\n")
            f.write("| !� | sG͔��(s) | P95͔��(s) | �� | sG,($) | (� |\n")
            f.write("|------|----------------|---------------|--------|------------|--------|\n")
            
            for model_key, results in provider_results.items():
                avg_response = statistics.mean([r.avg_response_time for r in results])
                avg_p95 = statistics.mean([r.p95_response_time for r in results])
                avg_success = statistics.mean([r.success_rate for r in results])
                avg_cost = statistics.mean([r.total_cost for r in results])
                
                quality_scores = []
                for r in results:
                    quality_scores.extend(r.quality_scores)
                avg_quality = statistics.mean(quality_scores) if quality_scores else 0
                
                f.write(f"| {model_key} | {avg_response:.2f} | {avg_p95:.2f} | "
                       f"{avg_success:.1%} | {avg_cost:.4f} | {avg_quality:.2f} |\n")
            
            # ��Ӝ
            f.write("\n## ��K�Ӝ\n")
            
            for model_key, results in provider_results.items():
                f.write(f"\n### {model_key}\n\n")
                
                for result in results:
                    test_name = TEST_CASES[result.test_case]['name']
                    f.write(f"#### {test_name}\n")
                    f.write(f"- ;�Bp: {result.total_requests}\n")
                    f.write(f"- �/1%: {result.successful_requests}/{result.failed_requests}\n")
                    f.write(f"- ͔��: sG {result.avg_response_time:.2f}s, "
                           f"P95 {result.p95_response_time:.2f}s\n")
                    f.write(f"- Token(: sG {result.avg_tokens:.0f}\n")
                    f.write(f"- ,: ${result.total_cost:.4f}\n")
                    if result.quality_scores:
                        f.write(f"- (��: {statistics.mean(result.quality_scores):.2f}\n")
                    if result.errors:
                        f.write(f"- �: {len(result.errors)}*\n")
                    f.write("\n")
            
            # �P
            f.write("\n## �P��\n\n")
            
            # ~� s'��!�
            best_value_models = self._find_best_value_models()
            f.write("###  s'��!�\n")
            for category, model in best_value_models.items():
                f.write(f"- {category}: {model}\n")
        
        print(f"\n�J��X0: {filename}")
    
    def _find_best_value_models(self) -> Dict[str, str]:
        """~�:o� s!�"""
        recommendations = {}
        
        # 	K�(��
        case_results = {}
        for result in self.results:
            if result.test_case not in case_results:
                case_results[result.test_case] = []
            case_results[result.test_case].append(result)
        
        # ��*(�
        for case, results in case_results.items():
            # ����Q�,(�	
            scores = []
            for r in results:
                if r.success_rate > 0.8:  # �Q��؄!�
                    # �� = (�C� * (� - ,C� * R , - ��C� * R ��
                    quality_score = statistics.mean(r.quality_scores) if r.quality_scores else 0
                    normalized_cost = r.total_cost / 0.1  # G�0.1�C:��
                    normalized_time = r.avg_response_time / 10  # G�10�:��
                    
                    score = 0.5 * quality_score - 0.3 * normalized_cost - 0.2 * normalized_time
                    scores.append((f"{r.provider}-{r.model}", score))
            
            if scores:
                best_model = max(scores, key=lambda x: x[1])[0]
                recommendations[TEST_CASES[case]['name']] = best_model
        
        return recommendations
    
    def plot_results(self):
        """�6'����"""
        # �pn
        model_names = []
        avg_response_times = []
        avg_costs = []
        avg_qualities = []
        
        # 	!�Zpn
        model_data = {}
        for result in self.results:
            key = f"{result.provider}-{result.model}"
            if key not in model_data:
                model_data[key] = {
                    "response_times": [],
                    "costs": [],
                    "qualities": []
                }
            
            model_data[key]["response_times"].extend(result.response_times)
            model_data[key]["costs"].append(result.total_cost)
            model_data[key]["qualities"].extend(result.quality_scores)
        
        # ��sG<
        for model, data in model_data.items():
            model_names.append(model.split('-')[1])  # �>:!�
            avg_response_times.append(statistics.mean(data["response_times"]))
            avg_costs.append(statistics.mean(data["costs"]))
            qualities = data["qualities"]
            avg_qualities.append(statistics.mean(qualities) if qualities else 0)
        
        # ��h
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
        
        # ͔����
        ax1.bar(model_names, avg_response_times, color='skyblue')
        ax1.set_ylabel('sG͔�� (�)')
        ax1.set_title('!�͔����')
        ax1.tick_params(axis='x', rotation=45)
        
        # ,��
        ax2.bar(model_names, avg_costs, color='lightcoral')
        ax2.set_ylabel('sG, ($)')
        ax2.set_title('!�(,��')
        ax2.tick_params(axis='x', rotation=45)
        
        # (����
        ax3.bar(model_names, avg_qualities, color='lightgreen')
        ax3.set_ylabel('sG(��')
        ax3.set_title('!���(���')
        ax3.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('model_performance_comparison.png', dpi=300, bbox_inches='tight')
        print("\n'������X0: model_performance_comparison.png")


async def run_model_performance_tests():
    """�L!�'�K�"""
    tester = ModelPerformanceTester()
    
    # �LK����!p��K�	
    await tester.test_all_models(test_iterations=5)


if __name__ == "__main__":
    print("DPA AI!�'���K�")
    print("="*60)
    print("K�!�")
    print("- OpenAI: GPT-4o, GPT-4o-mini, GPT-3.5-turbo")
    print("- Anthropic: Claude-3 Opus, Sonnet, Haiku")
    print("- DeepSeek: DeepSeek-Chat")
    print("="*60)
    
    asyncio.run(run_model_performance_tests())