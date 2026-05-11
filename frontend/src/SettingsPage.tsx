import { useState } from "react";

import { PageTabs } from "./PageTabs";

const settingsTabs = [
  { id: "profile", label: "Profile" },
  { id: "security", label: "Security" },
  { id: "notifications", label: "Notifications" },
  { id: "billing", label: "Billing" },
  { id: "preferences", label: "Preferences" },
];

export function SettingsPage() {
  const [activeTabId, setActiveTabId] = useState(settingsTabs[0].id);

  return (
    <section className="settings-page" aria-label="Settings">
      <PageTabs tabs={settingsTabs} activeTabId={activeTabId} onTabChange={setActiveTabId} label="Settings sections" />
      <div className="settings-page-body" />
    </section>
  );
}
