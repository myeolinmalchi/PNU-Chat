import {
  ChatContainer,
  ChatRequest,
  ChatResponse,
} from 'components/pages/chat';
import { Navigate } from 'react-router-dom';
import useChatDetail from 'hooks/useChatDetail';
import { ChatResponseHeader } from 'components/pages/chat/ChatResponse';

const Chat = () => {
  const { prevChat, uuid } = useChatDetail();

  if (!uuid) {
    return <Navigate to='/' />;
  }

  return (
    <>
      <ChatContainer>
        {prevChat?.messages.map((message) => {
          if (message.role === 'user' && message.content) {
            return <ChatRequest content={message.content} />;
          }

          if (message.role === 'assistant' && message.content) {
            return <ChatResponse content={message.content} />;
          }
        })}
        {prevChat?.question != null && (
          <>
            <ChatRequest content={prevChat.question} />
            {prevChat.error ? (
              <ChatResponse content={prevChat.error} error />
            ) : (
              <ChatResponseHeader pending />
            )}
          </>
        )}
      </ChatContainer>
    </>
  );
};

export default Chat;
