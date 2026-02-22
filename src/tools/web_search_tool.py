"""
联网搜索工具 - 用于获取薪酬数据、企业信息、行业趋势等外部信息
"""
import os
import requests
from typing import Optional
from cozeloop.decorator import observe
from coze_coding_utils.runtime_ctx.context import Context, default_headers
from langchain.tools import tool


@observe
def web_search(
        ctx: Context,
        query: str,
        search_type: str = "web",
        count: Optional[int] = 5,
        need_summary: Optional[bool] = True,
) -> tuple:
    """
    联网搜索API，返回搜索结果和总结
    使用 Brave Search API
    """
    # 使用 Brave Search API
    api_key = os.getenv("BRAVE_API_KEY", "")
    
    if not api_key:
        # 如果没有配置 API Key，返回模拟数据
        return [], f"搜索 '{query}' 的结果（模拟）:\n\n由于未配置 BRAVE_API_KEY，这里显示模拟搜索结果。"
    
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": api_key,
    }
    
    try:
        response = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": count},
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        # 提取搜索结果
        web_items = []
        results = data.get("web", {}).get("results", [])
        for item in results[:count]:
            web_items.append({
                "Title": item.get("title", ""),
                "Snippet": item.get("description", ""),
                "Url": item.get("url", "")
            })

        # 构建总结
        summary_parts = []
        for item in web_items[:3]:
            summary_parts.append(f"{item['Title']}: {item['Snippet']}")
        summary = "\n".join(summary_parts)
            
        return web_items, summary
        
    except requests.RequestException as e:
        raise Exception(f"网络请求失败: {str(e)}")
    except Exception as e:
        raise Exception(f"web_search 失败: {str(e)}")
    finally:
        if 'response' in locals():
            response.close()


@tool
def search_salary_info(query: str) -> str:
    """
    搜索薪酬信息

    Args:
        query: 薪酬查询关键词，例如"北京互联网产品经理薪资"或"深圳Java开发薪酬范围"

    Returns:
        str: 薪酬信息搜索结果
    """
    try:
        # 构建薪酬查询词
        salary_query = f"{query} 薪资 工资 待遇"
        
        web_items, summary = web_search(
            ctx=None,
            query=salary_query,
            search_type="web_summary",
            count=5,
            need_summary=True
        )
        
        if summary:
            return f"薪酬信息查询结果：\n\n{summary}\n\n参考数据来源："
        else:
            # 如果没有总结，返回搜索结果标题
            results = []
            for item in web_items[:3]:
                results.append(f"- {item.get('Title', '')}: {item.get('Snippet', '')}")
            
            if results:
                return "薪酬信息查询结果：\n\n" + "\n".join(results)
            else:
                return "未找到相关薪酬信息，请尝试更具体的查询词。"
                
    except Exception as e:
        return f"薪酬信息查询失败: {str(e)}"


@tool
def search_company_info(company_name: str) -> str:
    """
    搜索企业信息

    Args:
        company_name: 企业名称，例如"字节跳动"或"腾讯"

    Returns:
        str: 企业信息搜索结果
    """
    try:
        # 构建企业信息查询词
        company_query = f"{company_name} 公司 简介 规模 业务"
        
        web_items, summary = web_search(
            ctx=None,
            query=company_query,
            search_type="web_summary",
            count=5,
            need_summary=True
        )
        
        if summary:
            return f"企业信息查询结果：\n\n{summary}"
        else:
            # 如果没有总结，返回搜索结果标题
            results = []
            for item in web_items[:3]:
                results.append(f"- {item.get('Title', '')}: {item.get('Snippet', '')}")
            
            if results:
                return "企业信息查询结果：\n\n" + "\n".join(results)
            else:
                return f"未找到企业'{company_name}'的相关信息，请确认企业名称是否正确。"
                
    except Exception as e:
        return f"企业信息查询失败: {str(e)}"


@tool
def search_industry_trend(industry: str) -> str:
    """
    搜索行业趋势和岗位前景

    Args:
        industry: 行业名称或岗位类型，例如"互联网"、"人工智能"、"产品经理"

    Returns:
        str: 行业趋势信息
    """
    try:
        # 构建行业趋势查询词
        trend_query = f"{industry} 行业 发展趋势 前景 市场需求"
        
        web_items, summary = web_search(
            ctx=None,
            query=trend_query,
            search_type="web_summary",
            count=5,
            need_summary=True
        )
        
        if summary:
            return f"行业趋势查询结果：\n\n{summary}"
        else:
            # 如果没有总结，返回搜索结果标题
            results = []
            for item in web_items[:3]:
                results.append(f"- {item.get('Title', '')}: {item.get('Snippet', '')}")
            
            if results:
                return "行业趋势查询结果：\n\n" + "\n".join(results)
            else:
                return f"未找到行业'{industry}'的相关趋势信息，请尝试更具体的关键词。"
                
    except Exception as e:
        return f"行业趋势查询失败: {str(e)}"
