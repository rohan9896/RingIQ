type AuthErrorsProps = {
  messages: string[];
};

export function AuthErrors({ messages }: AuthErrorsProps) {
  if (messages.length === 0) {
    return null;
  }

  return (
    <div className="border-l-2 border-[#d73a2f] bg-[#f6e9e6] px-4 py-3 text-sm text-[#8f221c]">
      {messages.map((message, index) => (
        <p key={`${message}-${index}`}>{message}</p>
      ))}
    </div>
  );
}
