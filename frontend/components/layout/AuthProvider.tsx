"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("flowguard_token");
    
    const isAuthPage = pathname === "/login" || pathname === "/signup";

    if (!token && !isAuthPage) {
      router.replace("/login");
    } else if (token && isAuthPage) {
      router.replace("/dashboard");
    } else {
      setIsChecking(false);
    }
  }, [pathname, router]);

  if (isChecking) {
    return null; // Or a simple loading spinner
  }

  return <>{children}</>;
}
