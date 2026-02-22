import os
from langchain_core.runnables import RunnableConfig
from utils.log.common import get_execute_mode
from utils.log.node_log import Logger

# 可选：启用 CozeLoop 追踪（需要配置环境变量）
try:
    import cozeloop
    from cozeloop.integration.langchain.trace_callback import LoopTracer
    
    space_id = os.getenv("COZE_PROJECT_SPACE_ID", "")
    api_token = os.getenv("COZE_LOOP_API_TOKEN", "")
    base_url = os.getenv("COZE_LOOP_BASE_URL", "https://api.coze.cn")
    commit_hash = os.getenv("COZE_PROJECT_COMMIT_HASH", "")
    
    if space_id and api_token:
        cozeloopTracer = cozeloop.new_client(
            workspace_id=space_id,
            api_token=api_token,
            api_base_url=base_url,
        )
        cozeloop.set_default_client(cozeloopTracer)
        COZELOOP_ENABLED = True
    else:
        COZELOOP_ENABLED = False
        cozeloopTracer = None
except ImportError:
    COZELOOP_ENABLED = False
    cozeloopTracer = None


def init_run_config(graph, ctx):
    tracer = Logger(graph, ctx)
    tracer.on_chain_start = tracer.on_chain_start_graph
    tracer.on_chain_end = tracer.on_chain_end_graph
    
    callbacks = [tracer]
    
    # 如果启用了 CozeLoop，添加追踪回调
    if COZELOOP_ENABLED and cozeloopTracer:
        trace_callback_handler = LoopTracer.get_callback_handler(
            cozeloopTracer,
            add_tags_fn=tracer.get_node_tags,
            modify_name_fn=tracer.get_node_name,
            tags={
                "project_id": ctx.project_id,
                "execute_mode": get_execute_mode(),
                "log_id": ctx.logid,
                "commit_hash": os.getenv("COZE_PROJECT_COMMIT_HASH", ""),
            }
        )
        callbacks.append(trace_callback_handler)
    
    config = RunnableConfig(callbacks=callbacks)
    return config


def init_agent_config(graph, ctx):
    callbacks = []
    
    # 如果启用了 CozeLoop，添加追踪回调
    if COZELOOP_ENABLED and cozeloopTracer:
        from cozeloop.integration.langchain.trace_callback import LoopTracer
        callbacks.append(
            LoopTracer.get_callback_handler(
                cozeloopTracer,
                tags={
                    "project_id": ctx.project_id,
                    "execute_mode": get_execute_mode(),
                    "log_id": ctx.logid,
                    "commit_hash": os.getenv("COZE_PROJECT_COMMIT_HASH", ""),
                }
            )
        )
    
    config = RunnableConfig(callbacks=callbacks)
    return config


# 保留add_trace_tags函数，作为对trace.set_tags的简单包装
def add_trace_tags(trace, tags):
    """
    为trace添加标签
    :param trace: trace对象
    :param tags: 标签字典
    """
    if hasattr(trace, 'set_tags'):
        trace.set_tags(tags)

