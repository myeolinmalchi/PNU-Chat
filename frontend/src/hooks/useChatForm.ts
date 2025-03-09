import { useState } from 'react';
import { useChatStore } from 'stores/chatStore';
import { useNavigate } from 'react-router-dom';
import { useUserInfoStore } from 'stores/userInfoStore';

const useChatForm = () => {
  const [input, setInput] = useState('');
  const { sendQuestion, prevChat } = useChatStore();
  const { info } = useUserInfoStore();
  const pending = !!prevChat?.question || input === '';

  const navigate = useNavigate();

  const send = (question?: string) => {
    if (!info) {
      return;
    }

    if (!question && pending) {
      return;
    }
    const uuid = sendQuestion(question ?? input);

    setInput('');
    if (uuid !== null) {
      navigate(`/chats/${encodeURIComponent(uuid)}`);
    }
  };

  return {
    send,
    input,
    setInput,
    pending,
  };
};

export default useChatForm;
