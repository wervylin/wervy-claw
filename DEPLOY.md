# 上线部署指南

## 1. 基础设施准备

### 服务器/容器
- [ ] 准备云服务器（阿里云/腾讯云/AWS等）或 Kubernetes 集群
- [ ] 配置域名和 HTTPS 证书
- [ ] 设置防火墙和安全组规则

### 数据库
- [ ] 部署 PostgreSQL 数据库（如果使用持久化存储）
- [ ] 配置数据库备份策略
- [ ] 或使用托管数据库服务（如 RDS）

### 缓存/消息队列（可选）
- [ ] Redis（用于缓存、会话存储）
- [ ] 消息队列（如 RabbitMQ、Kafka，用于异步任务）

---

## 2. API Key 和密钥管理

### 必须配置的密钥
```bash
# Kimi API（核心功能必需）
KIMI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Brave Search API（联网搜索功能，可选）
BRAVE_API_KEY=

# 其他可选服务
COZE_PROJECT_SPACE_ID=      # CozeLoop 追踪（可选）
COZE_LOOP_API_TOKEN=        # CozeLoop 追踪（可选）
```

### 密钥管理建议
- [ ] **不要**把密钥硬编码在代码中
- [ ] 使用环境变量或密钥管理服务（如 AWS Secrets Manager、阿里云 KMS）
- [ ] 生产环境使用不同的 API Key
- [ ] 设置 API Key 使用限额和告警

---

## 3. 应用配置优化

### 性能优化
```python
# config/agent_llm_config.json
{
    "config": {
        "model": "kimi-k2-5",
        "temperature": 0.7,
        "max_completion_tokens": 8192,  # 根据需求调整
        "timeout": 120,  # 生产环境适当缩短
        "thinking": "disabled"
    }
}
```

### 并发和限流
- [ ] 配置合理的并发请求数
- [ ] 实现 API 限流（Rate Limiting）
- [ ] 设置请求超时时间

---

## 4. 部署方式选择

### 方案 A：Docker 部署（推荐）

创建 `Dockerfile`：
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY src/ ./src/
COPY config/ ./config/

# 环境变量
ENV COZE_WORKSPACE_PATH=/app
ENV COZE_PROJECT_TYPE=agent
ENV PYTHONPATH=/app/src

EXPOSE 5000

CMD ["python", "src/main.py", "-m", "http", "-p", "5000"]
```

创建 `docker-compose.yml`：
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - KIMI_API_KEY=${KIMI_API_KEY}
      - KIMI_BASE_URL=https://api.moonshot.cn/v1
      - BRAVE_API_KEY=${BRAVE_API_KEY}
    volumes:
      - ./logs:/tmp/work/logs
    restart: always
    
  # 可选：PostgreSQL
  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=app
      - POSTGRES_PASSWORD=your_password
      - POSTGRES_DB=jd_analyzer
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

volumes:
  postgres_data:
```

### 方案 B：Kubernetes 部署

创建 `k8s-deployment.yaml`：
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jd-analyzer
spec:
  replicas: 2  # 根据负载调整
  selector:
    matchLabels:
      app: jd-analyzer
  template:
    metadata:
      labels:
        app: jd-analyzer
    spec:
      containers:
      - name: app
        image: your-registry/jd-analyzer:latest
        ports:
        - containerPort: 5000
        env:
        - name: KIMI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: kimi-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: jd-analyzer-service
spec:
  selector:
    app: jd-analyzer
  ports:
  - port: 80
    targetPort: 5000
  type: LoadBalancer
```

### 方案 C：Serverless（如阿里云函数计算）
- 适合流量波动大的场景
- 按调用次数计费
- 需要适配函数计算的运行时

---

## 5. 监控和日志

### 日志管理
- [ ] 集中式日志收集（ELK、阿里云 SLS、Datadog）
- [ ] 日志分级（INFO/WARNING/ERROR）
- [ ] 日志保留策略（如保留 30 天）

### 监控告警
- [ ] 应用性能监控（APM）：响应时间、错误率
- [ ] 资源监控：CPU、内存、磁盘
- [ ] API 调用监控：Kimi API 使用量、费用
- [ ] 告警渠道：钉钉/飞书/邮件

### 健康检查
项目已内置 `/health` 接口，可用于负载均衡健康检查。

---

## 6. 安全加固

### 网络安全
- [ ] 启用 HTTPS（TLS 1.2+）
- [ ] 配置 CORS 白名单
- [ ] 使用 WAF（Web 应用防火墙）
- [ ] 限制 IP 访问（如有需要）

### 应用安全
- [ ] 输入验证和过滤
- [ ] 防止 SQL 注入（使用 ORM 参数化查询）
- [ ] 文件上传安全检查
- [ ] 敏感信息脱敏

### 数据安全
- [ ] 数据库加密（传输加密 + 存储加密）
- [ ] 定期备份
- [ ] 数据访问审计

---

## 7. 成本控制

### API 费用估算（Kimi）
| 模型 | 输入价格 | 输出价格 |
|------|---------|---------|
| kimi-k2-5 | ¥0.012/1K tokens | ¥0.06/1K tokens |

**估算示例**：
- 单次 JD 分析约 3K-5K tokens
- 日均 1000 次调用 ≈ ¥200-400/天

### 省钱策略
- [ ] 实现请求缓存（相同 JD 直接返回缓存结果）
- [ ] 设置用户调用配额
- [ ] 非核心功能降级（如关闭联网搜索）
- [ ] 使用更小的模型处理简单任务

---

## 8. 高可用设计

### 多实例部署
- [ ] 至少 2 个实例运行
- [ ] 负载均衡分发请求
- [ ] 滚动更新（零停机部署）

### 故障处理
- [ ] 数据库连接失败时自动降级到 MemorySaver
- [ ] API 限流时的优雅降级
- [ ] 超时处理

### 备份和恢复
- [ ] 数据库定期备份
- [ ] 配置文件版本控制
- [ ] 灾难恢复演练

---

## 9. 上线前检查清单

- [ ] 所有 API Key 已配置并测试
- [ ] 数据库连接正常
- [ ] 健康检查接口返回正常
- [ ] 日志收集正常
- [ ] 监控告警已配置
- [ ] 安全扫描通过
- [ ] 性能测试通过
- [ ] 回滚方案准备就绪

---

## 10. 推荐上线步骤

1. **第 1 周**：Docker 化 + 单机部署测试
2. **第 2 周**：添加监控和日志
3. **第 3 周**：安全加固 + 性能优化
4. **第 4 周**：多实例部署 + 灰度发布
5. **第 5 周**：全量上线 + 持续监控

---

## 需要我帮你做什么？

1. **创建 Dockerfile 和 docker-compose.yml**
2. **编写 Kubernetes 部署文件**
3. **配置 CI/CD 流水线**
4. **设置监控告警**
5. **性能优化**

告诉我你想先搞哪个？