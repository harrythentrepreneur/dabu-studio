export function CodeSnippet({ code }: { code: string }) {
  return (
    <pre className="bg-gray-100 dark:bg-gray-900 p-3 rounded text-sm">
      <code>{code}</code>
    </pre>
  );
}