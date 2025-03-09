import useUnivModal from 'hooks/useUnivModal';
import useUnivModalAnimation from 'hooks/useUnivModalAnimation';
import { ChangeEvent } from 'react';
import { twMerge } from 'tailwind-merge';

type InputSelectProps = {
  label: string;
  placeholder: string;
  className?: string;
  required?: boolean;
  disabled?: boolean;
  items?: string[];

  selected: string | null;
  handleSelect: (e: ChangeEvent<HTMLSelectElement>) => void;
};

const InputSelect = ({
  label,
  placeholder,
  className,
  required = true,
  disabled = false,
  items,

  selected,
  handleSelect,
}: InputSelectProps) => {
  return (
    <label
      className={twMerge(
        'w-full flex flex-col items-start justify-start gap-[6px]',
        className
      )}
    >
      <p className='text-[#494949] text-sm font-[600]'>
        {label}
        {required && <span className='ml-0.5 text-[#D54000]'>*</span>}
      </p>
      <div
        className={twMerge(
          'w-full px-3 py-3 flex flex-row justify-end rounded-[4px] border-[1px] border-[#D1D5D8]',
          disabled ? 'bg-gray-100' : ''
        )}
      >
        <select
          className='outline-none w-full appearance-none text-sm text-[#7A7A7A] bg-inherit'
          disabled={disabled}
          value={selected ?? ''}
          onChange={handleSelect}
        >
          <option value='' disabled hidden selected>
            {placeholder}
          </option>
          {items?.map((item) => <option value={item}>{item}</option>)}
        </select>
        <svg
          width='20'
          height='20'
          viewBox='0 0 24 24'
          fill='none'
          xmlns='http://www.w3.org/2000/svg'
        >
          <path
            d='M12.0006 14.1664C11.9103 14.1664 11.8264 14.1536 11.7486 14.128C11.6709 14.1024 11.5969 14.0586 11.5268 13.9965L8.16151 11.0109C8.05793 10.9189 8.00489 10.8032 8.0024 10.664C8.00002 10.5248 8.05306 10.407 8.16151 10.3107C8.27009 10.2145 8.40163 10.1664 8.55613 10.1664C8.71063 10.1664 8.84217 10.2145 8.95074 10.3107L12.0006 13.0166L15.0504 10.3107C15.1541 10.2188 15.2845 10.1718 15.4415 10.1695C15.5983 10.1674 15.7311 10.2145 15.8396 10.3107C15.9481 10.407 16.0023 10.5237 16.0023 10.6608C16.0023 10.7979 15.9481 10.9146 15.8396 11.0109L12.4744 13.9965C12.4042 14.0586 12.3303 14.1024 12.2525 14.128C12.1748 14.1536 12.0908 14.1664 12.0006 14.1664Z'
            fill='#BCC0C5'
          />
        </svg>
      </div>
    </label>
  );
};

const UnivModal = () => {
  const {
    submitEnabled,
    universities,
    departments,
    selected: { univ, department },
    handlers: { handleSelectUniv, handleSelectDepartment, handleSubmit },
  } = useUnivModal();

  const { zIndex, opacity, closeModal } = useUnivModalAnimation();

  return (
    <>
      <div
        className={twMerge(
          'absolute w-full h-full top-0 bg-[rgba(25,25,25,0.50)] transition-opacity duration-300',
          zIndex,
          opacity
        )}
      ></div>
      <div
        className={twMerge(
          'absolute w-[min(calc(100vw-40px),360px)] py-8 px-5 flex flex-col gap-0 items-center justify-center bg-white rounded-[12px]',
          zIndex,
          opacity
        )}
      >
        <span className='text-[#202020] w-full text-[18px] font-[600] mb-[28px]'>
          챗봇 이용을 위해
          <br />
          소속 단과대학 및 학과를 선택해주세요.
        </span>
        <InputSelect
          className='mb-[12px]'
          label='단과대학'
          placeholder='소속 단과대학을 선택해주세요.'
          items={universities ?? []}
          selected={univ}
          handleSelect={handleSelectUniv}
        />
        <InputSelect
          placeholder={'소속 학과를 선택해주세요.'}
          className='mb-[28px]'
          label='학과'
          disabled={!departments}
          items={departments ?? []}
          selected={department}
          handleSelect={handleSelectDepartment}
        />
        <div className='flex items-center justify-center gap-[6px] self-end'>
          <button
            onClick={handleSubmit}
            disabled={!submitEnabled}
            className='w-[92px] h-[32px] flex items-center justify-center active:bg-[#004785] transition-colors bg-[#005BAA] rounded-[4px] text-white text-[12px] font-[500] disabled:opacity-50'
          >
            확인
          </button>
          <button
            onClick={closeModal}
            className='w-[92px] h-[32px] flex items-center justify-center active:bg-gray-100 transition-colors bg-white rounded-[4px] border-[1px] border-[#D1D5D8] text-[#494949] text-[12px] font-[500]'
          >
            취소
          </button>
        </div>
      </div>
    </>
  );
};

export default UnivModal;
