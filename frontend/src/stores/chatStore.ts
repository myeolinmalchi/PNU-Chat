import { create } from 'zustand';
import {
  ChatContextType,
  ChatHistoryType,
  ChatListElementType,
  ChatRequestType,
  ChatResponseType,
} from 'types/chat';

import uuid from 'react-uuid';

import { useUserInfoStore } from './userInfoStore';

interface ChatState {
  chats: ChatListElementType[];
  prevChat: ChatContextType | null;
  abortController: AbortController;

  loadChatHistory: (uuid: string) => boolean;

  updateHistory: (res: ChatResponseType) => void;
  resetHistory: () => void;
  sendQuestion: (qeustion: string) => string | null;
}

const loadChatList = () => {
  const chatListString = localStorage.getItem('chats');

  if (!chatListString) {
    return [];
  }

  const chats: ChatListElementType[] = JSON.parse(chatListString);

  return chats;
};

export const useChatStore = create<ChatState>((set, get) => ({
  chats: loadChatList(),
  prevChat: null,
  abortController: new AbortController(),

  loadChatHistory: (uuid) => {
    const chatHistoryString = localStorage.getItem(`chat_${uuid}`);
    if (!chatHistoryString) {
      return false;
    }

    const chatHistory: ChatHistoryType = JSON.parse(chatHistoryString);

    set((prev) => ({
      ...prev,
      prevChat: {
        uuid,
        ...chatHistory,
        question: null,
      },
    }));

    return true;
  },

  updateHistory: (res) => {
    const prevChat = get().prevChat;
    if (!prevChat) return;

    const uuid = prevChat.uuid;

    const chatHistory: ChatHistoryType = {
      messages: res.messages,
      //contexts: res.contexts,
      contexts: [],
    };

    const exists = get().chats.filter((c) => c.uuid === uuid).length > 0;
    if (!exists) {
      const chats = [
        { title: res.title ?? '', uuid, createdAt: new Date() },
        ...get().chats,
      ];
      localStorage.setItem('chats', JSON.stringify(chats));
      set((prev) => ({ ...prev, chats }));
    }

    localStorage.setItem(`chat_${uuid}`, JSON.stringify(chatHistory));

    set((prev) => ({
      ...prev,
      prevChat: { ...prevChat, ...chatHistory, question: null },
    }));
  },

  resetHistory: () => {
    if (get().prevChat?.question != null) {
      get().abortController.abort();
      set((prev) => ({ ...prev, abortController: new AbortController() }));
    }
    set((prev) => ({ ...prev, prevChat: null }));
  },

  sendQuestion: (question) => {
    const userInfo = useUserInfoStore.getState().info;
    if (userInfo === null) {
      throw Error('사용자 정보가 없습니다.');
    }

    const prevChat = get().prevChat;

    if (prevChat?.question != null) {
      get().abortController.abort();
    }

    const newChat: ChatContextType = prevChat
      ? { ...prevChat, question }
      : {
          uuid: uuid(),
          question,
          messages: [],
          contexts: [],
        };

    set((prev) => ({ ...prev, prevChat: newChat }));

    const body: ChatRequestType = {
      question,
      model: 'gpt-4o-mini',
      messages: newChat.messages,
      //contexts: newChat.contexts,
      contexts: [],
      ...userInfo,
    };

    fetch('/api/chat', {
      method: 'post',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      signal: get().abortController.signal,
    })
      .then((res) => {
        if (res.ok) {
          return res.json();
        }
        throw Error;
      })
      .then((body) => {
        const chatResponse: ChatResponseType = body;
        get().updateHistory(chatResponse);
      })
      .catch((e) => {
        if (e.name === 'AbortError') return;
        set((prev) => ({ ...prev, prevChat: { ...newChat, error: true } }));
      });

    return prevChat ? null : newChat.uuid;
  },
}));
