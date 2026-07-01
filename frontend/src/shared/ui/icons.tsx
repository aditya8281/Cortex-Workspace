import type { ReactNode } from "react";

interface IconProps {
  className?: string;
  size?: number;
}

type IconComponent = (props: IconProps) => ReactNode;

function Svg({
  children,
  className,
  size = 18,
  viewBox = "0 0 18 18",
}: {
  children: ReactNode;
  className?: string;
  size?: number;
  viewBox?: string;
}) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox={viewBox}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

// ── Mode icons ────────────────────────────────────────────────────────

export const ChatIcon: IconComponent = (props) => (
  <Svg {...props} viewBox="0 0 18 18">
    <path d="M3 3h12a1 1 0 011 1v8a1 1 0 01-1 1H6l-3 3V4a1 1 0 011-1z" />
  </Svg>
);

export const SearchIcon: IconComponent = (props) => (
  <Svg {...props}>
    <circle cx="7.5" cy="7.5" r="5" />
    <path d="M11.5 11.5L15 15" />
  </Svg>
);

export const BrainIcon: IconComponent = (props) => (
  <Svg {...props} viewBox="0 0 18 18">
    <path d="M9 3C7 3 5 4.5 5 7c0 1.5.7 2.8 1.8 3.7-.3.8-.8 1.5-1.4 2a2 2 0 00.6 3.3 2 2 0 003-1.5H9c1 0 2-.5 2.6-1.3" />
    <path d="M13 3c2 0 4 1.5 4 4 0 1.5-.7 2.8-1.8 3.7.3.8.8 1.5 1.4 2a2 2 0 01-.6 3.3 2 2 0 01-3-1.5H9" />
    <path d="M9 9V5.5M9 9l-2 2M9 9l2 2" />
  </Svg>
);

export const VaultIcon: IconComponent = (props) => (
  <Svg {...props}>
    <rect x="3" y="8" width="12" height="7" rx="1" />
    <path d="M5.5 8V5.5a3.5 3.5 0 117 0V8" />
    <circle cx="9" cy="11.5" r=".75" fill="currentColor" stroke="none" />
    <path d="M9 11.5v2" />
  </Svg>
);

export const ModelsIcon: IconComponent = (props) => (
  <Svg {...props}>
    <rect x="2" y="3" width="14" height="12" rx="1" />
    <path d="M6 3v12M10 3v12M14 3v12M2 7h14M2 11h14" />
  </Svg>
);

export const CodeIcon: IconComponent = (props) => (
  <Svg {...props}>
    <path d="M6 5L2 9l4 4M12 5l4 4-4 4M9 3l-2 12" />
  </Svg>
);

export const UtilityIcon: IconComponent = (props) => (
  <Svg {...props}>
    <circle cx="9" cy="9" r="2.5" />
    <path d="M9 4.5V3M9 15v-1.5M13.5 9H15M3 9h1.5M12 6l1-1M5 13l1-1M12 12l1 1M5 5l1 1" />
  </Svg>
);

export const SettingsIcon: IconComponent = (props) => (
  <Svg {...props}>
    <circle cx="9" cy="9" r="2" />
    <path d="M9 2.5V4M9 14v1.5M15 9h-1.5M4.5 9H3M13 5l1-1M4 14l1-1M13 13l1 1M4 4l1 1" />
    <path d="M7.3 2.7l.3-1.2h2.8l.3 1.2a6.5 6.5 0 011.2.7l1-.5 2 2-.5 1a6.5 6.5 0 01.7 1.2l1.2.3v2.8l-1.2.3a6.5 6.5 0 01-.7 1.2l.5 1-2 2-1-.5a6.5 6.5 0 01-1.2.7l-.3 1.2H7.6l-.3-1.2a6.5 6.5 0 01-1.2-.7l-1 .5-2-2 .5-1a6.5 6.5 0 01-.7-1.2L2.7 10.6V7.8l1.2-.3a6.5 6.5 0 01.7-1.2l-.5-1 2-2 1 .5a6.5 6.5 0 011.2-.7z" />
  </Svg>
);

export const SystemsIcon: IconComponent = (props) => (
  <Svg {...props}>
    <rect x="2" y="3" width="14" height="10" rx="1" />
    <path d="M6 16h6M9 13v3" />
    <circle cx="5.5" cy="7" r=".75" fill="currentColor" stroke="none" />
    <circle cx="8" cy="7" r=".75" fill="currentColor" stroke="none" />
    <circle cx="10.5" cy="7" r=".75" fill="currentColor" stroke="none" />
  </Svg>
);

export const ProfileIcon: IconComponent = (props) => (
  <Svg {...props}>
    <circle cx="9" cy="6.5" r="3" />
    <path d="M3 16c0-3 2.7-5.5 6-5.5s6 2.5 6 5.5" />
  </Svg>
);

// ── Action icons ──────────────────────────────────────────────────────

export const LightningIcon: IconComponent = (props) => (
  <Svg {...props}>
    <path d="M10 1L4 10h4l-1 7 7-10h-4l1-7-7 10" />
  </Svg>
);

export const HomeIcon: IconComponent = (props) => (
  <Svg {...props}>
    <path d="M2 9l7-6 7 6" />
    <path d="M4 7.5V15a1 1 0 001 1h3v-4h2v4h3a1 1 0 001-1V7.5" />
  </Svg>
);

export const CloseIcon: IconComponent = (props) => (
  <Svg {...props}>
    <path d="M5 5l8 8M13 5l-8 8" />
  </Svg>
);

export const PaperclipIcon: IconComponent = (props) => (
  <Svg {...props}>
    <path d="M10 3.5L5.5 8a3 3 0 004.2 4.2l4.5-4.5a1.5 1.5 0 00-2.1-2.1L5.5 10" />
  </Svg>
);

export const MicIcon: IconComponent = (props) => (
  <Svg {...props}>
    <rect x="6.5" y="1" width="5" height="9" rx="2.5" />
    <path d="M3 8.5a6 6 0 0012 0M9 15v2" />
  </Svg>
);

export const SendIcon: IconComponent = (props) => (
  <Svg {...props}>
    <path d="M2 9l12-6-6 12-2-4-4-2z" />
  </Svg>
);

export const StopIcon: IconComponent = (props) => (
  <Svg {...props}>
    <rect x="3" y="3" width="12" height="12" rx="1.5" fill="currentColor" stroke="none" />
  </Svg>
);

export const MenuIcon: IconComponent = (props) => (
  <Svg {...props}>
    <path d="M2 4h14M2 9h14M2 14h10" />
  </Svg>
);

export const PlusIcon: IconComponent = (props) => (
  <Svg {...props}>
    <path d="M9 2v14M2 9h14" />
  </Svg>
);

export const EditIcon: IconComponent = (props) => (
  <Svg {...props}>
    <path d="M13 1.5l2.5 2.5L6 13.5H3.5V11L13 1.5z" />
  </Svg>
);

export const TrashIcon: IconComponent = (props) => (
  <Svg {...props}>
    <path d="M3 4h12M6 4V2.5a.5.5 0 01.5-.5h3a.5.5 0 01.5.5V4M4 4l1 10h8l1-10" />
  </Svg>
);

export const BackIcon: IconComponent = (props) => (
  <Svg {...props}>
    <path d="M11 3L5 9l6 6" />
  </Svg>
);

export const DocumentIcon: IconComponent = (props) => (
  <Svg {...props}>
    <path d="M5 2h5l4 4v9a1 1 0 01-1 1H5a1 1 0 01-1-1V3a1 1 0 011-1z" />
    <path d="M10 2v4h4" />
  </Svg>
);

export const BrainIconAlt: IconComponent = (props) => (
  <Svg {...props}>
    <path d="M4 7c0-2.2 1.8-4 4-4s4 1.8 4 4" />
    <path d="M4 7a3 3 0 00-1 2.3A2 2 0 005 11h.5" />
    <path d="M14 7a3 3 0 011 2.3A2 2 0 0113 11h-.5" />
    <path d="M7 14v-3a2 2 0 014 0v3" />
    <path d="M6.5 14h3" />
  </Svg>
);

export const BoltIcon: IconComponent = (props) => (
  <Svg {...props}>
    <path d="M8 1L3 10h5l-1 7 7-10H9l1-7-7 10" />
  </Svg>
);
