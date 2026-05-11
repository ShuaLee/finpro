import { SettingsPage } from "./SettingsPage";

type MainContentProps = {
  page: "home" | "settings";
};

export function MainContent({ page }: MainContentProps) {
  return <main className="main-content" data-page={page}>{page === "settings" ? <SettingsPage /> : null}</main>;
}
