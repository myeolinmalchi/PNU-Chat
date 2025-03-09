import { useEffect } from 'react';
import { useChatStore } from 'stores/chatStore';
import { useParams } from 'react-router-dom';
import { useNavigate } from 'react-router-dom';

const useChatDetail = () => {
  const { loadChatHistory, resetHistory, prevChat, abortController } =
    useChatStore();
  const navigate = useNavigate();

  const { uuid } = useParams();

  useEffect(() => {
    if (!uuid) {
      resetHistory();
      return;
    }

    const pending = prevChat?.question != null;

    const chatExists = loadChatHistory(uuid);

    if (pending && chatExists) {
      abortController.abort();
    }

    if (!pending && !chatExists) {
      navigate('/');
    }
  }, [uuid]);

  return {
    uuid,
    prevChat,
  };
};

export default useChatDetail;
