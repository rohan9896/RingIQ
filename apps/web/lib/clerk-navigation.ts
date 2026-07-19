export type ClerkNavigationLocation = {
  assign: (href: string) => void;
};

export function postAuthDestination(
  currentTaskKey: string | null | undefined,
  destination: string,
  organizationTaskDestination = "/workspace/setup",
) {
  return currentTaskKey === "choose-organization"
    ? organizationTaskDestination
    : destination;
}

export function navigateWithClerk(
  url: string,
  navigate: (href: string) => void,
  navigationLocation: ClerkNavigationLocation = window.location,
) {
  if (url.startsWith("https://") || url.startsWith("http://")) {
    navigationLocation.assign(url);
    return;
  }

  navigate(url);
}
