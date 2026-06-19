"use client";

import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import { type ReactNode } from "react";
import { cn } from "../../lib/utils";

interface DropdownProps {
  trigger: ReactNode;
  children: ReactNode;
  align?: "start" | "center" | "end";
}

export default function Dropdown({ trigger, children, align = "end" }: DropdownProps) {
  return (
    <DropdownMenuPrimitive.Root>
      <DropdownMenuPrimitive.Trigger asChild>
        {trigger}
      </DropdownMenuPrimitive.Trigger>
      <DropdownMenuPrimitive.Portal>
        <DropdownMenuPrimitive.Content
          align={align}
          sideOffset={6}
          className={cn(
            "z-50 min-w-[180px] rounded-xl bg-bg-elevated border border-border-subtle p-1.5",
            "shadow-elevated animate-fade-in-scale"
          )}
        >
          {children}
        </DropdownMenuPrimitive.Content>
      </DropdownMenuPrimitive.Portal>
    </DropdownMenuPrimitive.Root>
  );
}

export function DropdownItem({
  children,
  className,
  destructive,
  ...props
}: DropdownMenuPrimitive.DropdownMenuItemProps & { destructive?: boolean }) {
  return (
    <DropdownMenuPrimitive.Item
      className={cn(
        "flex items-center gap-2 rounded-lg px-3 py-2 text-sm cursor-pointer outline-none transition-colors",
        "text-text-secondary hover:bg-bg-hover hover:text-text",
        destructive && "text-error hover:bg-error-muted",
        className
      )}
      {...props}
    >
      {children}
    </DropdownMenuPrimitive.Item>
  );
}

export function DropdownSeparator() {
  return <DropdownMenuPrimitive.Separator className="my-1 h-px bg-border-subtle" />;
}
