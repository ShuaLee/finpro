type PageTab = {
  id: string;
  label: string;
};

type PageTabsProps = {
  tabs: PageTab[];
  activeTabId: string;
  onTabChange: (tabId: string) => void;
  label: string;
};

export function PageTabs({ tabs, activeTabId, onTabChange, label }: PageTabsProps) {
  return (
    <nav className="page-tabs" aria-label={label}>
      <div className="page-tabs-list" role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`page-tab ${tab.id === activeTabId ? "page-tab-active" : ""}`.trim()}
            role="tab"
            aria-selected={tab.id === activeTabId}
            onClick={() => onTabChange(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
    </nav>
  );
}
