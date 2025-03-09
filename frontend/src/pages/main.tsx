import { ChatExample, Logo } from 'components/pages/main';

const chatExamples = {
  '휴학 신청 기간': '2025년 1학기 휴학 신청 기간을 알려주세요.',
  '졸업 유예 조건': '졸업 유예를 위해서 어떤 조건을 충족해야 하나요?',
  '국가장학금 수혜 조건': '국가장학금 수혜 조건이 어떻게 되나요?',
  '캡스톤 디자인': '캡스톤 디자인 교과목에 대해 설명해주세요.',
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
