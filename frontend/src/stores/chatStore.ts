import { create } from 'zustand';
import uuid from 'react-uuid';

import {
  ChatContextType,
  ChatHistoryType,
  ChatListElementType,
  ChatRequestType,
  ChatResponseType,
} from 'types/chat';

import { useUserInfoStore } from './userInfoStore';

// ------------------------------------------------------
// 설정값들
// ------------------------------------------------------
/** 최대 요청 횟수 (예: 일주일간 15회만 가능) */
const MAX_REQUEST_LIMIT = 15;

/** 만료 기간(ms). 아래는 7일 예시 (7 * 24 * 60 * 60 * 1000) */
const EXPIRE_INTERVAL_MS = 7 * 24 * 60 * 60 * 1000;

/** chat 목록을 localStorage에서 가져오기 */
function loadChatList(): ChatListElementType[] {
  const chatListString = localStorage.getItem('chats');
  if (!chatListString) {
    return [];
  }
  return JSON.parse(chatListString) as ChatListElementType[];
}

function formatTimestampToDateString(timestamp: number): string {
  const date = new Date(timestamp);

  const year = date.getFullYear();
  // JS에서 getMonth()는 0부터 시작하므로 1 더해주고, 2자리 형식 보장
  const month = String(date.getMonth() + 1).padStart(2, '0');
  // getDate()는 이미 1부터 시작. 2자리 형식 보장
  const day = String(date.getDate()).padStart(2, '0');

  return `${year}-${month}-${day}`;
}

// ------------------------------------------------------
// requestCount + expiresAt를 묶어서 localStorage에 저장/로드
// ------------------------------------------------------
interface RequestData {
  count: number; // 현재까지 사용한 요청 횟수
  expiresAt: number; // 만료 시각 (timestamp, ms)
}

/** requestData를 localStorage에서 로드 */
function loadRequestData(): RequestData {
  try {
    const dataString = localStorage.getItem('requestData');
    if (!dataString) {
      // 초기값: count=0, expiresAt=현재+7일
      return {
        count: 0,
        expiresAt: Date.now() + EXPIRE_INTERVAL_MS,
      };
    }
    const parsed = JSON.parse(dataString) as RequestData;
    return parsed;
  } catch (e) {
    // 파싱 실패 시 초기값
    console.log(e);
    return {
      count: 0,
      expiresAt: Date.now() + EXPIRE_INTERVAL_MS,
    };
  }
}

/** requestData를 localStorage에 저장 */
function saveRequestData(data: RequestData) {
  localStorage.setItem('requestData', JSON.stringify(data));
}

interface ChatState {
  // -------------------------
  // 기존 상태
  // -------------------------
  chats: ChatListElementType[];
  prevChat: ChatContextType | null;
  abortController: AbortController;

  loadChatHistory: (uuid: string) => boolean;
  updateHistory: (res: ChatResponseType) => void;
  resetHistory: () => void;
  sendQuestion: (question: string) => string | null;

  // -------------------------
  // 추가된 만료 관련 상태
  // -------------------------
  requestCount: number; // 현재까지의 요청 횟수
  expiresAt: number; // 만료 시점

  /** 만료 확인 후, 요청 가능하면 카운트 1 증가 */
  checkAndIncrementRequestCount: () => boolean;
}

export const useChatStore = create<ChatState>((set, get) => {
  // ------------------------------------------------------
  // 초기화 시점에 localStorage에서 requestData 로드
  // ------------------------------------------------------
  const { count, expiresAt } = loadRequestData();
  let initialCount = count;
  let initialExpiresAt = expiresAt;

  // 만약 만료 시간이 이미 지난 경우라면, 카운트를 0으로 리셋하고 새 만료 시간 설정
  const now = Date.now();
  if (now > expiresAt) {
    initialCount = 0;
    initialExpiresAt = now + EXPIRE_INTERVAL_MS;
    saveRequestData({ count: initialCount, expiresAt: initialExpiresAt });
  }

  return {
    // -------------------------
    // 기본 상태
    // -------------------------
    chats: loadChatList(),
    prevChat: null,
    abortController: new AbortController(),

    loadChatHistory: (uuid: string) => {
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

    updateHistory: (res: ChatResponseType) => {
      const prevChat = get().prevChat;
      if (!prevChat) return;
      const uuid = prevChat.uuid;

      const chatHistory: ChatHistoryType = {
        messages: res.messages,
        // contexts: res.contexts,
        contexts: [],
      };

      const exists = get().chats.some((c) => c.uuid === uuid);
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

    sendQuestion: (question: string) => {
      // 유저 정보 불러오기
      const userInfo = useUserInfoStore.getState().info;
      if (!userInfo) {
        throw Error('사용자 정보가 없습니다.');
      }

      // 진행 중인 질문이 있다면 abort
      const prevChat = get().prevChat;
      if (prevChat?.question != null) {
        get().abortController.abort();
      }

      // 새 채팅 or 기존 채팅
      const newChat: ChatContextType = prevChat
        ? { ...prevChat, question }
        : {
            uuid: uuid(),
            question,
            messages: [],
            contexts: [],
          };

      const canIncrement = get().checkAndIncrementRequestCount();
      if (!canIncrement) {
        const msg = `요청 한도를 초과했습니다. ${formatTimestampToDateString(
          get().expiresAt
        )}부터 다시 사용 가능합니다.`;

        set((prev) => ({
          ...prev,
          prevChat: { ...newChat, error: msg },
        }));

        return newChat.uuid;
      }

      // prevChat 갱신
      set((prev) => ({ ...prev, prevChat: newChat }));

      const body: ChatRequestType = {
        uuid: newChat.uuid,
        question,
        model: 'gpt-4o-mini',
        messages: newChat.messages,
        // contexts: newChat.contexts,
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
          throw Error('서버 응답이 실패했습니다.');
        })
        .then((body) => {
          const chatResponse: ChatResponseType = body;
          get().updateHistory(chatResponse);
        })
        .catch((e) => {
          if (e.name === 'AbortError') return;
          set((prev) => ({
            ...prev,
            prevChat: { ...newChat, error: e.message },
          }));
        });

      // 새 채팅이면 uuid 반환, 아니면 null
      return prevChat ? null : newChat.uuid;
    },

    // -------------------------
    // 만료시간 포함한 요청 횟수 로직
    // -------------------------
    requestCount: initialCount,
    expiresAt: initialExpiresAt,

    checkAndIncrementRequestCount: () => {
      const state = get();
      const now = Date.now();

      // 만료 시간이 지났다면 리셋
      if (now > state.expiresAt) {
        // 새 만료시간 + 카운트=0
        const newExpiresAt = now + EXPIRE_INTERVAL_MS;
        set({
          requestCount: 0,
          expiresAt: newExpiresAt,
        });
        saveRequestData({
          count: 0,
          expiresAt: newExpiresAt,
        });
      }

      // 다시 state 가져옴(리셋 후 값이 바뀌었을 수 있으므로)
      const { requestCount, expiresAt } = get();
      if (requestCount >= MAX_REQUEST_LIMIT) {
        // 이미 한도 초과
        return false;
      }

      // 카운트를 1 증가시킴
      const newCount = requestCount + 1;
      set({ requestCount: newCount });
      saveRequestData({ count: newCount, expiresAt });
      return true;
    },
  };
});
