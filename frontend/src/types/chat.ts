import { UserInfoType } from './user';

type ChatListElementType = {
  title: string;
  uuid: string;
  createdAt: Date;
};

type ChatMessageType = {
  seq: number;
  role: 'user' | 'assistant' | 'tool';
  content: string | null;
  tool_call_id?: string;
};

type SearchHistoryType = {
  content: string[];
  tool_name: string;
  tool_args: object;
};

type TokenUsageType = {
  prompt_tokens: number;
  completion_tokens: number;
  cached_prompt_tokens: number;
  total_tokens: number;
};

type ChatRequestType = UserInfoType & {
  question: string;
  model?: 'gpt-4o' | 'o3-mini' | 'gpt-4o-mini';
  messages: ChatMessageType[];
  contexts: SearchHistoryType[];
};

type ChatResponseType = {
  title: string | null;
  answer: string;
  question: string;
  messages: ChatMessageType[];
  contexts: SearchHistoryType[];
  usage: TokenUsageType;
};

type ChatContextType = {
  uuid: string;
  error?: string;
  messages: ChatMessageType[];
  contexts: SearchHistoryType[];
  question: string | null;
};

type ChatHistoryType = {
  messages: ChatMessageType[];
  contexts: SearchHistoryType[];
};

export type {
  ChatRequestType,
  ChatResponseType,
  ChatListElementType,
  ChatMessageType,
  ChatHistoryType,
  ChatContextType,
};
