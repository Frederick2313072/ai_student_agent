import {
  App as AntdApp,
  Card,
  ConfigProvider,
  theme,
  Button,
  Space,
  Tooltip,
} from "antd";
import {
  RobotOutlined,
  UserOutlined,
  CopyOutlined,
  ReloadOutlined,
  LikeOutlined,
  DislikeOutlined,
  ShareAltOutlined,
} from "@ant-design/icons";
import { Bubble, Sender, useXAgent, useXChat } from "@ant-design/x";
import type { GetProp } from "antd";
import { useRef, useState, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { atomDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import "./App.css";

// 后端 API 地址
const API_URL = "http://localhost:8000/chat";

// 示例提示问题
const examplePrompts = [
  {
    title: "学习概念",
    question: "请帮我理解什么是深度学习？",
  },
  {
    title: "解释原理",
    question: "能解释一下机器学习的工作原理吗？",
  },
  {
    title: "实际应用",
    question: "人工智能在日常生活中有哪些应用？",
  },
];

// Markdown组件配置
const MarkdownComponents: any = {
  code: (props: any) => {
    const { inline, className, children } = props;
    const match = /language-(\w+)/.exec(className || "");
    return !inline && match ? (
      <SyntaxHighlighter style={atomDark} language={match[1]} PreTag="div">
        {String(children).replace(/\n$/, "")}
      </SyntaxHighlighter>
    ) : (
      <code
        className={className}
        style={{
          background: "rgba(255,255,255,0.1)",
          padding: "2px 4px",
          borderRadius: "4px",
          color: "#ffffff",
        }}
      >
        {children}
      </code>
    );
  },
  p: (props: any) => (
    <p style={{ color: "rgba(255,255,255,0.9)", margin: "8px 0" }}>
      {props.children}
    </p>
  ),
  h1: (props: any) => (
    <h1 style={{ color: "#ffffff", fontSize: "1.5em", marginBottom: "16px" }}>
      {props.children}
    </h1>
  ),
  h2: (props: any) => (
    <h2 style={{ color: "#ffffff", fontSize: "1.3em", marginBottom: "12px" }}>
      {props.children}
    </h2>
  ),
  h3: (props: any) => (
    <h3 style={{ color: "#ffffff", fontSize: "1.1em", marginBottom: "8px" }}>
      {props.children}
    </h3>
  ),
  ul: (props: any) => (
    <ul style={{ color: "rgba(255,255,255,0.9)", paddingLeft: "20px" }}>
      {props.children}
    </ul>
  ),
  ol: (props: any) => (
    <ol style={{ color: "rgba(255,255,255,0.9)", paddingLeft: "20px" }}>
      {props.children}
    </ol>
  ),
  li: (props: any) => (
    <li style={{ color: "rgba(255,255,255,0.9)", marginBottom: "4px" }}>
      {props.children}
    </li>
  ),
  blockquote: (props: any) => (
    <blockquote
      style={{
        borderLeft: "4px solid #1677ff",
        paddingLeft: "16px",
        margin: "16px 0",
        background: "rgba(22,119,255,0.1)",
        color: "rgba(255,255,255,0.9)",
      }}
    >
      {props.children}
    </blockquote>
  ),
  strong: (props: any) => (
    <strong style={{ color: "#ffffff", fontWeight: "600" }}>
      {props.children}
    </strong>
  ),
  em: (props: any) => (
    <em style={{ color: "rgba(255,255,255,0.9)" }}>{props.children}</em>
  ),
};

// 消息操作按钮组件
const MessageActions = ({
  content,
  isAI,
}: {
  content: string;
  isAI: boolean;
}) => {
  const handleCopy = () => {
    navigator.clipboard.writeText(content);
  };

  const handleRegenerate = () => {
    // 重新生成逻辑，这里可以调用父组件的方法
    console.log("重新生成");
  };

  const handleLike = () => {
    console.log("点赞");
  };

  const handleDislike = () => {
    console.log("点踩");
  };

  const handleShare = () => {
    console.log("分享");
  };

  return (
    <div className="message-actions">
      <Space size="small">
        <Tooltip title="复制">
          <Button
            type="text"
            size="small"
            icon={<CopyOutlined />}
            onClick={handleCopy}
            className="action-button"
          />
        </Tooltip>

        {isAI && (
          <>
            <Tooltip title="重新生成">
              <Button
                type="text"
                size="small"
                icon={<ReloadOutlined />}
                onClick={handleRegenerate}
                className="action-button"
              />
            </Tooltip>

            <Tooltip title="有用">
              <Button
                type="text"
                size="small"
                icon={<LikeOutlined />}
                onClick={handleLike}
                className="action-button"
              />
            </Tooltip>

            <Tooltip title="无用">
              <Button
                type="text"
                size="small"
                icon={<DislikeOutlined />}
                onClick={handleDislike}
                className="action-button"
              />
            </Tooltip>
          </>
        )}

        <Tooltip title="分享">
          <Button
            type="text"
            size="small"
            icon={<ShareAltOutlined />}
            onClick={handleShare}
            className="action-button"
          />
        </Tooltip>
      </Space>
    </div>
  );
};

// 自定义消息内容渲染组件
const MessageContent = ({
  content,
  role,
}: {
  content: string;
  role: string;
}) => {
  const isAI = role === "ai";

  return (
    <div className="message-wrapper">
      <div
        className="message-content"
        style={{ color: "rgba(255,255,255,0.95)" }}
      >
        {isAI ? (
          <ReactMarkdown components={MarkdownComponents}>
            {content}
          </ReactMarkdown>
        ) : (
          <div style={{ color: "rgba(255,255,255,0.95)" }}>{content}</div>
        )}
      </div>
      <MessageActions content={content} isAI={isAI} />
    </div>
  );
};

// 定义角色样式 - 参考 Gemini 设计
const roles: GetProp<typeof Bubble.List, "roles"> = {
  ai: {
    placement: "start",
    avatar: {
      icon: <RobotOutlined />,
      style: {
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        color: "white",
      },
    },
    style: {
      maxWidth: 600,
    },
  },
  user: {
    placement: "end",
    avatar: {
      icon: <UserOutlined />,
      style: {
        background: "#1677ff",
        color: "white",
      },
    },
  },
};

// 加载状态的不同阶段
const loadingStages = [
  "正在理解您的问题...",
  "正在分析知识点和疑点...",
  "正在查询相关知识库...",
  "正在生成针对性问题...",
  "正在整理回复内容...",
];

const App = () => {
  const sessionId = useRef(uuidv4());
  const [currentLoadingStage, setCurrentLoadingStage] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);

  // 模拟加载阶段的进度
  useEffect(() => {
    let interval: number;
    if (isProcessing) {
      interval = setInterval(() => {
        setCurrentLoadingStage((prev) => {
          if (prev < loadingStages.length - 1) {
            return prev + 1;
          }
          return prev;
        });
      }, 1500); // 每1.5秒切换到下一个阶段
    } else {
      setCurrentLoadingStage(0);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isProcessing]);

  const [agent] = useXAgent({
    request: async (info, callbacks) => {
      const { message, messages } = info;
      const { onSuccess, onError } = callbacks;

      setIsProcessing(true);

      try {
        const response = await fetch(API_URL, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            topic: "通用对话",
            explanation: message,
            session_id: sessionId.current,
            short_term_memory: (messages || []).map((msg: string) => ({
              type: "human",
              content: msg,
            })),
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const aiResponse =
          data.questions && data.questions.length > 0
            ? data.questions.join("\n\n")
            : "抱歉，我现在无法回答您的问题。";

        setIsProcessing(false);
        onSuccess(aiResponse);
      } catch (error) {
        console.error("请求失败:", error);
        setIsProcessing(false);
        onError(error instanceof Error ? error : new Error(String(error)));
      }
    },
  });

  const { onRequest, messages } = useXChat({
    agent,
    requestPlaceholder: loadingStages[currentLoadingStage],
    requestFallback: "抱歉，请求失败了，请稍后重试。",
  });

  return (
    <ConfigProvider
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: "#1677ff",
        },
      }}
    >
      <AntdApp>
        <div className="app">
          <div className="chat-container">
            <div className="chat-header">
              <h1>AI 费曼学习助手</h1>
            </div>

            <div className="chat-content">
              {messages.length === 0 ? (
                <div className="welcome-container">
                  <div className="welcome-title">AI 费曼学习助手</div>
                  <div className="welcome-subtitle">今天我能帮您做些什么？</div>
                  <div className="prompts-grid">
                    {examplePrompts.map((prompt) => (
                      <Card
                        key={prompt.title}
                        size="small"
                        hoverable
                        className="prompt-card"
                        onClick={() => onRequest(prompt.question)}
                      >
                        <div className="prompt-title">{prompt.title}</div>
                        <div className="prompt-question">{prompt.question}</div>
                      </Card>
                    ))}
                  </div>
                </div>
              ) : (
                <Bubble.List
                  roles={roles}
                  style={{ maxHeight: 500, padding: "16px" }}
                  items={messages.map(({ id, message, status }) => ({
                    key: id,
                    loading: status === "loading",
                    role: status === "local" ? "user" : "ai",
                    content: (
                      <MessageContent
                        content={message}
                        role={status === "local" ? "user" : "ai"}
                      />
                    ),
                  }))}
                />
              )}
            </div>

            <Sender
              placeholder="输入您的问题……"
              onSubmit={onRequest}
              loading={agent.isRequesting()}
            />
          </div>
        </div>
      </AntdApp>
    </ConfigProvider>
  );
};

export default App;
