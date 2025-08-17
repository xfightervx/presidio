import ActionItem from "./ActionItem";

export default function ColumnCard({ column, actions, onFeedback }) {
  return (
    <div className="border rounded-xl shadow p-4 bg-white mb-4">
      <h2 className="text-lg font-bold mb-2">{column}</h2>
      {actions.map((action, idx) => (
        <ActionItem
          key={idx}
          action={action}
          column={column}
          onChange={onFeedback}
        />
      ))}
    </div>
  );
}
