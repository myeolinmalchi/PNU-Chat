import logo from 'assets/images/logo.png';
import file from 'assets/images/icons/file.svg';
import link from 'assets/images/icons/link.svg';
//import refresh from 'assets/images/icons/refresh.svg';

import ReactMarkdown from 'react-markdown';
import React, { useEffect, useState } from 'react';

const ChatResponseHeader = ({ pending }: { pending: boolean }) => {
  const basePlaceholder = '답변 생성중';
  const [pendingPlaceholder, setPendingPlaceholder] = useState(basePlaceholder);

  useEffect(() => {
    let dots = '';
    const interval = setInterval(() => {
      dots = dots.length >= 3 ? '.' : dots + '.';
      setPendingPlaceholder(`${basePlaceholder}${dots}`);
    }, 300);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className='flex flex-row justify-start items-center gap-4'>
      <img className='w-[min(8.889vw,44px)] aspect-square' src={logo} alt='' />
      {pending && (
        <span className='text-[14px] font-[400] text-[#7A7A7A]'>
          {pendingPlaceholder}
        </span>
      )}
    </div>
  );
};

type ChatResponseProps = {
  content: string;
  error?: boolean;
};

const ChatResponse = ({ content, error }: ChatResponseProps) => {
  return (
    <div className='w-full flex justify-start flex-col gap-3 mb-5 last:mb-0'>
      <ChatResponseHeader pending={false} />
      <span className='w-full max-w-full text-chat-response text-[16px] font-[500] bg-none rounded-xl break-words break-all prose'>
        {error == true ? (
          <>답변을 불러올 수 없습니다. 잠시 후 다시 시도하세요.</>
        ) : (
          <ReactMarkdown
            components={{
              a: (props) => {
                const linkText = React.Children.toArray(props.children).join(
                  ''
                );
                const linkUrl = props.href;

                if (!linkUrl) {
                  return;
                }

                if (linkText === 'FILE' || linkUrl.includes('download')) {
                  return (
                    <a
                      target='_blank'
                      className='inline-block align-middle'
                      {...props}
                    >
                      <img className='ml-1 mt-0 mb-[2px]' src={file} alt='' />
                    </a>
                  );
                }
                return (
                  <a
                    target='_blank'
                    className='inline-block align-middle'
                    {...props}
                  >
                    <img className='ml-1 mt-0 mb-[2px]' src={link} alt='' />
                  </a>
                );
              },
            }}
          >
            {content}
          </ReactMarkdown>
        )}
      </span>
    </div>
  );
};

export default ChatResponse;
export { ChatResponseHeader };
