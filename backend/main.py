# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, Optional
from io import BytesIO
from transformers import AutoProcessor, Gemma3nForConditionalGeneration
import time
import os
import json
import base64
import matplotlib.pyplot as plt
import numpy as np

from core.storage import save_mood_entry, get_mood_history, export_history
from core.emotional_chat_function import EmotionalChatHandler
from core.emotion_analyzer_enhanced import EmotionAnalyzer
from utils.multi_plutchik_plotter import PlutchikPlotter

print("🧠 当前运行文件：", os.path.abspath(__file__))
print("🧠 当前 Python 进程 PID:", os.getpid())
print("🧠 当前文件最后修改时间:", time.ctime(os.path.getmtime(__file__)))

MODEL = None
PROCESSOR = None
CHAT_HANDLER = None
# 添加快速测试模式
QUICK_TEST_MODE = False  # 🔧 跳过LLM分析，只测试接口

def get_chat_handler():
    global CHAT_HANDLER
    if CHAT_HANDLER is None:
        MODEL, PROCESSOR = get_models()
        CHAT_HANDLER = EmotionalChatHandler(MODEL, PROCESSOR)
    return CHAT_HANDLER

def get_models():
    """懒加载模型，只在第一次使用时加载"""
    global MODEL, PROCESSOR
    if MODEL is None or PROCESSOR is None:
        print("🔄 正在加载模型...")
        model_id = "google/gemma-3n-e2b-it"
        MODEL = Gemma3nForConditionalGeneration.from_pretrained(model_id).to("cpu").eval()
        PROCESSOR = AutoProcessor.from_pretrained(model_id)
        print("✅ 模型加载完成")
    return MODEL, PROCESSOR

app = FastAPI(
    title="Emotion Plugin API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 挂载前端静态文件
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# 添加主页路由
@app.get("/")
async def read_index():
    return FileResponse('../frontend/index.html')

# 添加CORS中间件，允许所有来源跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 或指定前端地址如 ["http://127.0.0.1:5500"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MoodInput(BaseModel):
    text: str
    use_llm: bool = True
    save: bool = False  # 前端按钮传入，决定是否保存
    enable_conversation: bool = False  # 新增
    conversation_id: Optional[str] = None  # 新增

class MoodRecord(BaseModel):
    timestamp: str
    input_mood: str
    mood_category: str





@app.post("/chat")
def chat_with_agent(mood_input: MoodInput):
    # 🔧 快速测试模式
    if QUICK_TEST_MODE:
        if mood_input.conversation_id:
            # 继续对话的简单回复
            ai_response = f"后端收到继续对话: '{mood_input.text}'"
            return {
                "timestamp": datetime.now().isoformat(),
                "conversation_enabled": True,
                "conversation_id": mood_input.conversation_id,
                "ai_response": ai_response
            }
        else:
            # 新对话
            # 创建测试图片
           
            fig, ax = plt.subplots(figsize=(6, 6))
            
            # 绘制一个简单的情绪轮盘测试图
            emotions = ['joy', 'trust', 'fear', 'surprise', 'sadness', 'disgust', 'anger', 'anticipation']
            values = [0.3, 0.5, 0.2, 0.8, 0.6, 0.1, 0.4, 0.7]
            colors = ['gold', 'green', 'blue', 'pink', 'navy', 'lightgreen', 'red', 'orange']
            
            # 创建极坐标图
            angles = np.linspace(0, 2*np.pi, len(emotions), endpoint=False).tolist()
            values += values[:1]  # 闭合图形
            angles += angles[:1]
            
            ax = plt.subplot(111, projection='polar')
            ax.plot(angles, values, 'o-', linewidth=2, color='navy')
            ax.fill(angles, values, alpha=0.25, color='lightblue')
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(emotions)
            ax.set_ylim(0, 1)
            ax.set_title('Test Emotion Wheel', y=1.08)
            
            plt.tight_layout()
            
            # 转换为base64
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
            buf.seek(0)
            test_image = base64.b64encode(buf.read()).decode('utf-8')
            buf.close()
            plt.close()
            return {
                "timestamp": datetime.now().isoformat(),
                "intensity_labels": {"joy": "Joy", "sadness": "Sadness"},
                "emotion_scores": {"joy": 4, "sadness": 2},
                "emotion_reasons": {"joy": "reason1", "sadness": "reason2"},
                "plutchik_image": test_image,
                "conversation_enabled": True,
                "conversation_id": "backend_test_123",
                "ai_response": "response from backend test"
            }
    user_text = mood_input.text
    # mood_result = classify_mood_with_gemma3(user_text,save_result=mood_input.save)
    timestamp = datetime.now().isoformat()

    MODEL, PROCESSOR = get_models()
    if not mood_input.conversation_id:
        analyzer = EmotionAnalyzer(user_text, MODEL, PROCESSOR, save_result=mood_input.save)
            
        # 绘制情绪图表（即使没有情绪也能生成空图表）
        emotion_sets = [analyzer.normalized, analyzer.blended_emotions]
        plotter = PlutchikPlotter(emotion_sets)
        
        fig = plotter.draw_multiple_plutchik_wheels(return_fig=True)
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", transparent=True)
        buf.seek(0)
        base64_image = base64.b64encode(buf.read()).decode("utf-8")
        buf.close()

        result = {
                "timestamp": timestamp,
                "input_mood": user_text,
                
                # 🔧 修正字段映射
                "intensity_labels": analyzer.classification,     # 前端需要的强度标签
                "emotion_scores": analyzer.base_scores,          # 前端需要的基础评分
                "emotion_reasons": analyzer.emotion_reasons,      # 情绪原因说明
                
                # 保留其他有用字段
                "normalized_emotions": analyzer.normalized,       # 标准化情绪
                "blended_emotions": analyzer.blended_emotions,    # 混合情绪
                "plutchik_image": base64_image,                  # 情绪图表
                
                # 对话字段默认值
                "conversation_enabled": False,
                "conversation_id": None,
                "ai_response": None
            }
    else:
        # 继续对话时的简化结果
        result = {
            "timestamp": timestamp,
            "input_mood": user_text,
            "conversation_continue": True,
            # 保持对话字段的默认值
            "conversation_enabled": False,
            "conversation_id": None,
            "ai_response": None
        }

    if mood_input.enable_conversation:
        try:
            #chat_handler = EmotionalChatHandler(MODEL, PROCESSOR)
            chat_handler = get_chat_handler()  # 使用全局实例
            
            if mood_input.conversation_id:
                # 继续对话
                print(f"🔧 继续对话，ID: {mood_input.conversation_id}")
                print(f"🔧 当前存储的对话: {getattr(chat_handler, 'active_conversations', {}).keys()}")
                ai_response = chat_handler.continue_emotional_conversation(
                    mood_input.conversation_id, user_text
                )
                conversation_id = mood_input.conversation_id
            else:
                # 开始新对话
                emotion_info = analyzer.emotion_info
                reference_response = analyzer.emotion_reasons
                conversation_id, ai_response = chat_handler.start_emotional_conversation(
                    user_text, emotion_info, reference_response
                )
            
            # 添加对话相关字段
            result.update({
                "conversation_enabled": True,
                "conversation_id": conversation_id,
                "ai_response": ai_response
            })
            
        except Exception as e:
            print(f"❌ 对话功能出错: {e}")
            result.update({
                "conversation_enabled": False,
                "conversation_error": str(e)
            })
    return result



@app.get("/history")
def view_history() -> Dict[str, Any]:
    records = get_mood_history()

    return {"records": records}

@app.get("/stats")
def mood_stats() -> Dict[str, Any]:
    records = get_mood_history()
    # 这里可以添加统计和可视化逻辑
    stats = {}  # TODO: 实现统计
    return {"stats": stats}

@app.get("/export")
def export_diary(format: str = "csv") -> Dict[str, Any]:
    records = get_mood_history()
    file_content = export_history(records, format)
    return {"file": file_content, "format": format}



if __name__ == "__main__":
    import uvicorn
    import webbrowser
    import threading
    import time
    
    def open_browser():
        time.sleep(2)  # 等待服务器启动
        webbrowser.open('http://localhost:8888')
    
    # 启动浏览器线程
    threading.Thread(target=open_browser, daemon=True).start()
    
    print("🚀 启动服务器...")
    print("🌐 应用将在 http://localhost:8888 自动打开")
    
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8888,
        reload=True
    )

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         "main:app",
#         host="127.0.0.1",
#         port=8888,
#         reload=True
#     )
