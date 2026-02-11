import os
import json
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(
        api_key=api_key,
        base_url="https://llm-new-api.makelove.expert/v1/"
    )

def translate_paper_all_in_one(title, abstract):
    client = get_openai_client()
    if not client:
        logger.warning("Warning: OPENAI_API_KEY not set, skipping translation")
        return {
            "title": title,
            "abstract": abstract,
            "summary": "一篇关于音频处理的研究论文。",
            "tags": []
        }

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是专业的学术翻译助手，擅长音乐信息检索和音频处理领域。请返回JSON格式的结果。"},
                {"role": "user", "content": f"""请翻译以下论文并生成一句话总结和主题标签：

标题：{title}

摘要：{abstract}

请返回JSON格式：
{{
    "title": "翻译后的中文标题",
    "abstract": "翻译后的中文摘要",
    "summary": "用最简单的话概括论文核心内容（20字以内）",
    "tags": ["标签1", "标签2", "标签3"]
}}

要求：
- 标签应该概括论文的主题领域，例如：深度学习、音频生成、语音识别、音乐理解、声音分离等
- 生成3-4个相关标签
- 标签要简短精确"""}
            ],
            temperature=0.3,
            max_tokens=800
        )

        result_text = response.choices[0].message.content.strip()
        result_text = result_text.replace('```json', '').replace('```', '').strip()
        result = json.loads(result_text)

        return {
            "title": result.get("title", title),
            "abstract": result.get("abstract", abstract),
            "summary": result.get("summary", "一篇关于音频处理的研究论文。"),
            "tags": result.get("tags", [])
        }
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return {
            "title": title,
            "abstract": abstract,
            "summary": "一篇关于音频处理的研究论文。",
            "tags": []
        }


def translate_title(text):
    if not text or len(text.strip()) < 3:
        return text

    client = get_openai_client()
    if not client:
        logger.warning("Warning: OPENAI_API_KEY not set, skipping title translation")
        return text

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是一个专业的学术翻译助手。请将论文标题翻译成简洁的中文，保持专业性。"},
                {"role": "user", "content": f"请将以下论文标题翻译成中文：{text}"}
            ],
            temperature=0.3,
            max_tokens=100
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Title translation error: {e}")
        return text

def translate_abstract(text, source_language="en", target_language="zh"):
    if not text or len(text.strip()) < 20:
        return text

    client = get_openai_client()
    if not client:
        logger.warning("Warning: OPENAI_API_KEY not set, skipping abstract translation")
        return text

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是一个专业的学术翻译助手，擅长翻译音乐信息检索和音频处理领域的论文摘要。请保持专业术语的准确性。"},
                {"role": "user", "content": f"请将以下英文摘要翻译成中文：\n\n{text}"}
            ],
            temperature=0.3,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Abstract translation error: {e}")
        return text

def generate_summary(title, abstract):
    if not title or not abstract:
        return "一篇关于音频处理的研究论文。"

    client = get_openai_client()
    if not client:
        return "一篇关于音频处理的研究论文。"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是一个学术论文总结助手。请用一句简单易懂的话（20字以内）概括论文的核心内容，面向普通读者。"},
                {"role": "user", "content": f"论文标题：{title}\n\n摘要：{abstract}\n\n请用一句话总结："}
            ],
            temperature=0.5,
            max_tokens=50
        )
        summary = response.choices[0].message.content.strip()
        summary = summary.replace('"', '').replace('"', '').replace('"', '')
        return summary
    except Exception as e:
        logger.error(f"Summary generation error: {e}")
        return "一篇关于音频处理的研究论文。"
