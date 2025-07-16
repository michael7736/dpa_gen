"use client"

import { Header } from "@/components/layout/header"
import { Sidebar } from "@/components/layout/sidebar"
import { useStore } from "@/store/useStore"

export default function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const isSidebarOpen = useStore((state) => state.isSidebarOpen)
  
  return (
    <>
      <Header />
      <div className="relative h-[calc(100vh-4rem)]">
        <Sidebar />
        <main 
          className="h-full overflow-y-auto transition-all duration-200"
          style={{
            marginLeft: isSidebarOpen ? '256px' : '0'
          }}
        >
          {children}
        </main>
      </div>
    </>
  )
}