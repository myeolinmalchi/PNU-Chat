import { ChatExample, Logo } from 'components/pages/main';

const chatExamples = {
  '휴학 신청 기간': '휴학 신청은 언제 할 수 있나요?',
  '졸업 유예 횟수': '졸업 유예는 최대 몇 번까지 할 수 있나요?',
  '프리미어 장학금 유지 조건': '프리미어 장학금 유지 조건이 어떻게 되나요?',
  '졸업 학점': '졸업을 위해 몇학점을 이수해야 하나요?',
  '군휴학 후 일반휴학 전환 가능 여부':
    '군휴학이 끝나고 일반휴학을 연달아서 할 수 있나요?',
  '수강정정 기간': '2025년 1학기 수강정정 기간은 언제인가요?',
  '수강취소 유의사항': '수강취소 관련해서 유의할 점이 있나요?',
};

const Main = () => {
  return (
    <>
      <Logo />
      <ChatExample.Container>
        {Object.entries(chatExamples).map(([preview, question]) => (
          <ChatExample preview={preview} question={question} />
        ))}
      </ChatExample.Container>
    </>
  );
};

export default Main;
