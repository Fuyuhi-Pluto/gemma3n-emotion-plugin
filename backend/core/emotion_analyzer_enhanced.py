# emotion_analyzer_enhanced.py

import re
import os
import datetime
from typing import Dict, List, Tuple, Optional
from difflib import get_close_matches
from utils.emotion_utils import BASIC_EMOTIONS, EMOTION_REPLACEMENTS, INTENSITY_MAP, DYAD_DICT, standardize_emotions, detect_blend_emotions
from utils.dynamic_prompt_builder import EmotionAnalysisPromptBuilder
import torch


class EmotionAnalyzer:
    def __init__(self, text: str, model=None, processor=None, auto_analyze: bool = True, save_result: bool = False):
        """
        Enhanced emotion analyzer
        
        Args:
            text: Text to analyze
            model: LLM model instance
            processor: Model processor
            auto_analyze: Whether to automatically perform analysis (default True)
            save_result: Whether to save analysis results to file (default False)
        """
        self.text = text
        self.model = model
        self.processor = processor
        self.save_result = save_result
        
        # Analysis results
        self.raw_response = None
        self.emotion_info = {}
        self.reference_response = ""
        self.saved_file_path = None  # Save file path
        
        # Original attributes (filled after analyze)
        self.emotion_scores = {}
        self.emotion_reasons = {}
        self.standardized = {}
        self.base_scores = {}
        self.normalized = {}
        self.blended_emotions = {}
        self.classification = {}
        
        # If no model provided, try to use global models
        if self.model is None or self.processor is None:
            self._load_global_models()
        
        # Auto analyze
        if auto_analyze:
            self.analyze()
    
    def _load_global_models(self):
        """Try to load global models"""
        try:
            from ..utils.mood_classifier_gemma3 import MODEL, PROCESSOR
            if self.model is None:
                self.model = MODEL
            if self.processor is None:
                self.processor = PROCESSOR
        except ImportError:
            raise ValueError("Model and processor must be provided or available globally")
    
    def _llm_analyze_emotion(self) -> str:
        """
        Internal method: Use LLM to analyze emotions
        """
        if self.model is None or self.processor is None:
            raise ValueError("Model and processor are required for analysis")
        
        builder = EmotionAnalysisPromptBuilder()
        messages = builder.build_messages(self.text)
        
        inputs = self.processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt"
        ).to(self.model.device)
        
        input_len = inputs["input_ids"].shape[-1]
        
        with torch.inference_mode():
            generation = self.model.generate(
                **inputs, 
                max_new_tokens=300, 
                do_sample=False,
                pad_token_id=self.processor.tokenizer.eos_token_id if hasattr(self.processor, 'tokenizer') else None
            )
            generation = generation[0][input_len:]
        
        decoded = self.processor.decode(generation, skip_special_tokens=True)
        return decoded.strip()
    
    def _extract_emotion_info_from_response(self, response: str) -> Tuple[Dict[str, Dict[str, str]], str]:
        """
        Internal method: Extract emotion information from LLM response
        """
        emotion_dict = {}
        
        # 提取情绪信息
        match = re.search(r'basic_emotions:\s*((?:\n\s*-\s*[a-zA-Z]+:.*)+)', response)
        if match:
            lines = match.group(1).strip().splitlines()
            for line in lines:
                m = re.match(r'\s*-\s*([a-zA-Z_]+):\s*intensity\s*=\s*(\d+),\s*reason\s*=\s*"([^"]*)"', line)
                if m:
                    emotion = m.group(1).lower()
                    intensity = int(m.group(2))
                    reason = m.group(3).strip()
                    emotion_dict[emotion] = {'intensity': intensity, 'reason': reason}
        
        # 提取参考回复
        companion_match = re.search(r'companion_response:\s*(.+)', response, re.DOTALL)
        reference_response = companion_match.group(1).strip() if companion_match else ""
        
        return emotion_dict, reference_response
    
    def analyze(self) -> 'EmotionAnalyzer':
        """
        Perform complete emotion analysis
        
        Returns:
            self: Support method chaining
        """
        try:
            # 1. LLM分析
            self.raw_response = self._llm_analyze_emotion()
            
            # 2. 提取情绪信息
            self.emotion_info, self.reference_response = self._extract_emotion_info_from_response(self.raw_response)
            
            # 3. 处理情绪数据（原有逻辑）
            self.emotion_scores = {k: v["intensity"] for k, v in self.emotion_info.items()}
            self.emotion_reasons = {k: v["reason"] for k, v in self.emotion_info.items()}
            self.standardized = standardize_emotions(self.emotion_scores)
            self.base_scores = self._fill_base_emotions()
            self.normalized = self._normalize()
            self.blended_emotions = detect_blend_emotions(self.normalized)
            self.classification = self.classify_intensity()
            
            # 4. 根据设置决定是否保存
            if self.save_result:
                self.saved_file_path = self.save_response()
                print(f"✅ Analysis results saved to: {self.saved_file_path}")
            
        except Exception as e:
            print(f"❌ Emotion analysis failed: {e}")
            # 设置默认值
            self._set_default_values()
        
        return self
    
    def _set_default_values(self):
        """设置默认值（分析失败时）"""
        self.emotion_info = {}
        self.emotion_scores = {}
        self.emotion_reasons = {}
        self.standardized = {}
        self.base_scores = {}
        self.normalized = {}
        self.blended_emotions = {}
        self.classification = {}
        self.reference_response = ""
    
    def save_response(self, mood_dir: str = None) -> str:
        """
        Save analysis results to file
        
        Args:
            mood_dir: Save directory, if None use default directory
            
        Returns:
            Saved file path
        """
        if mood_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            mood_dir = os.path.join(current_dir, "../Mood")
            print(f"🔍 Debug info:")
            print(f"  __file__: {__file__}")
            print(f"  current_dir: {current_dir}")
            print(f"  mood_dir: {mood_dir}")
            print(f"  Directory exists: {os.path.exists(mood_dir)}")
        
        os.makedirs(mood_dir, exist_ok=True)
        
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        existing_files = [f for f in os.listdir(mood_dir) if f.startswith(date_str + "Mood_") and f.endswith(".txt")]
        
        max_num = 0
        for fname in existing_files:
            match = re.match(rf"{date_str}Mood_(\d+)\.txt", fname)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
        
        # 总是创建新文件（递增编号）
        target_num = max_num + 1
        
        file_path = os.path.join(mood_dir, f"{date_str}Mood_{target_num}.txt")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Input Mood: {self.text}\n\n")
            if self.raw_response:
                f.write(self.raw_response)
        
        return file_path
    
    def force_save(self, mood_dir: str = None) -> str:
        """
        强制保存分析结果（即使初始化时设置了不保存）
        
        Args:
            mood_dir: 保存目录
            
        Returns:
            保存的文件路径
        """
        self.saved_file_path = self.save_response(mood_dir)
        print(f"✅ Analysis results force saved to: {self.saved_file_path}")
        return self.saved_file_path
    
    def get_emotion_dict_for_chat(self) -> Dict[str, Dict[str, any]]:
        """
        Get emotion dictionary format suitable for chat system
        
        Returns:
            Formatted emotion dictionary
        """
        return self.emotion_info
    
    def has_valid_emotions(self) -> bool:
        """Check if there are valid emotion analysis results"""
        return bool(self.emotion_info)
    
    # 原有的方法保持不变
    def _fill_base_emotions(self):
        """原有方法"""
        has_base = any(emo in BASIC_EMOTIONS for emo in self.emotion_scores)
        if not has_base:
            return {}
        result = {emo: 0.0 for emo in BASIC_EMOTIONS}
        for emo, val in self.emotion_scores.items():
            if emo in result:
                result[emo] = val
        return result

    def _normalize(self, scores=None):
        """原有方法"""
        if scores is None:
            scores = self.base_scores
        norm = {emo: ((val) / 5 if val != 0 else 0.0) for emo, val in scores.items()}
        return norm

    def classify_intensity(self) -> Dict[str, Tuple[str, str]]:
        """原有方法"""
        result = {}
        for emo, score in self.base_scores.items():
            if emo not in INTENSITY_MAP or score == 0:
                continue
            if score <= 2:
                label = INTENSITY_MAP[emo][0]
            elif score == 3:
                label = INTENSITY_MAP[emo][1]
            else:
                label = INTENSITY_MAP[emo][2]
            result[emo] = label
        return result

    def summary(self) -> Dict:
        """返回完整的分析摘要"""
        return {
            "text": self.text,
            "emotions": self.emotion_scores,
            "reasons": self.emotion_reasons,
            "reference_response": self.reference_response,
            "standardized": self.standardized,
            "base_scores": self.base_scores,
            "normalized": self.normalized,
            "intensity_classification": self.classification,
            "blended_emotions": self.blended_emotions,
            "raw_response": self.raw_response,
            "saved_file_path": self.saved_file_path,
            "was_saved": self.save_result
        }


# 兼容性：保留原有的函数接口
def create_emotion_analyzer_from_dict(emotion_info: Dict[str, Dict[str, str]]) -> EmotionAnalyzer:
    """
    Create analyzer from emotion dictionary (backward compatibility)
    
    Args:
        emotion_info: Emotion information in original format
        
    Returns:
        EmotionAnalyzer instance
    """
    analyzer = EmotionAnalyzer("", auto_analyze=False, save_result=False)  # Don't auto analyze, don't save
    analyzer.emotion_info = emotion_info
    analyzer.emotion_scores = {k: v["intensity"] for k, v in emotion_info.items()}
    analyzer.emotion_reasons = {k: v["reason"] for k, v in emotion_info.items()}
    analyzer.standardized = standardize_emotions(analyzer.emotion_scores)
    analyzer.base_scores = analyzer._fill_base_emotions()
    analyzer.normalized = analyzer._normalize()
    analyzer.blended_emotions = detect_blend_emotions(analyzer.normalized)
    analyzer.classification = analyzer.classify_intensity()
    return analyzer


# 使用示例
def demo_usage():
    """使用示例"""
    print("=== Refactored EmotionAnalyzer Usage Example ===\n")
    
    text = "I'm graduating next week. I'm so proud but really going to miss this place."
    
    print("Method 1: Analyze but don't save (default)")
    print("analyzer = EmotionAnalyzer(text)")
    print("# Auto analyze, don't save file\n")
    
    print("Method 2: Analyze and save")
    print("analyzer = EmotionAnalyzer(text, save_result=True)")
    print("# Auto analyze and save to file\n")
    
    print("Method 3: Manual control")
    print("analyzer = EmotionAnalyzer(text, auto_analyze=False)")
    print("analyzer.analyze()  # Manual analysis")
    print("analyzer.force_save()  # Force save\n")
    
    print("Method 4: Fully customized")
    print("analyzer = EmotionAnalyzer(text, model, processor, auto_analyze=True, save_result=True)")
    print("# Specify model, auto analyze, auto save\n")
    
    print("Get results:")
    print("emotion_dict = analyzer.get_emotion_dict_for_chat()")
    print("reference_response = analyzer.reference_response")
    print("summary = analyzer.summary()")
    print("was_saved = analyzer.saved_file_path is not None")

if __name__ == "__main__":
    demo_usage()
