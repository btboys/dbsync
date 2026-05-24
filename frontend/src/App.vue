<template>
  <div class="app-shell">
    <!-- Mobile overlay -->
    <div v-if="isMobile && mobileMenuOpen" class="mobile-overlay" @click="mobileMenuOpen = false" />

    <!-- Mobile header bar -->
    <header class="mobile-header">
      <button class="mobile-menu-btn" @click="mobileMenuOpen = !mobileMenuOpen">
        <t-icon name="view-list" />
      </button>
      <span class="mobile-logo">DBSync</span>
    </header>

    <!-- Sidebar -->
    <aside :class="['sidebar', { 'mobile-open': mobileMenuOpen, 'mobile-hidden': isMobile && !mobileMenuOpen }]">
      <div class="sidebar-brand">
        <div class="sidebar-logo">D</div>
        <span class="sidebar-title">DBSync</span>
      </div>
      <nav class="sidebar-nav">
        <router-link v-for="item in navItems" :key="item.value" :to="item.to" class="nav-item" :class="{ active: activeRoute === item.value }" @click="isMobile && (mobileMenuOpen = false)">
          <t-icon :name="item.icon" class="nav-icon" />
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <span class="sidebar-version">v0.1.0</span>
      </div>
    </aside>

    <!-- Main content -->
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const activeRoute = computed(() => route.path.split("/")[1] || "dashboard");

const isMobile = ref(false);
const mobileMenuOpen = ref(false);

const navItems = [
  { value: "dashboard", to: "/", icon: "dashboard", label: "仪表盘" },
  { value: "datasources", to: "/datasources", icon: "server", label: "数据源" },
  { value: "backup", to: "/backup", icon: "backup", label: "备份" },
  { value: "migration", to: "/migration", icon: "swap", label: "迁移" },
  { value: "schedules", to: "/schedules", icon: "time", label: "定时策略" },
  { value: "logs", to: "/logs", icon: "file", label: "日志" },
];

function checkMobile() {
  isMobile.value = window.innerWidth <= 768;
}

onMounted(() => {
  checkMobile();
  window.addEventListener("resize", checkMobile);
});

onUnmounted(() => {
  window.removeEventListener("resize", checkMobile);
});
</script>

<style>
.app-shell {
  display: flex;
  min-height: 100vh;
  background: var(--ds-bg);
}

/* Sidebar */
.sidebar {
  width: 240px;
  min-width: 240px;
  background: var(--ds-sidebar-bg);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  height: 100vh;
  z-index: 100;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 24px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.sidebar-logo {
  width: 36px;
  height: 36px;
  background: var(--ds-primary);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Fira Code', monospace;
  font-weight: 700;
  font-size: 18px;
  color: #fff;
}

.sidebar-title {
  font-family: 'Fira Code', monospace;
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  letter-spacing: -0.02em;
}

.sidebar-nav {
  flex: 1;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 6px;
  color: var(--ds-sidebar-text);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: var(--ds-transition);
  cursor: pointer;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.nav-item.active {
  background: var(--ds-primary);
  color: #fff;
}

.nav-icon {
  font-size: 18px;
  width: 18px;
  height: 18px;
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.sidebar-version {
  font-family: 'Fira Code', monospace;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.3);
}

/* Main content */
.main-content {
  flex: 1;
  padding: 24px;
  min-width: 0;
  overflow-x: hidden;
}

/* Mobile header */
.mobile-header {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 52px;
  background: var(--ds-sidebar-bg);
  z-index: 101;
  align-items: center;
  padding: 0 16px;
  gap: 12px;
}

.mobile-logo {
  font-family: 'Fira Code', monospace;
  font-size: 16px;
  font-weight: 700;
  color: #fff;
}

.mobile-menu-btn {
  background: none;
  border: none;
  color: #fff;
  font-size: 22px;
  padding: 6px;
  cursor: pointer;
  border-radius: 6px;
  display: flex;
  align-items: center;
  transition: var(--ds-transition);
}

.mobile-menu-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.mobile-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 99;
}

/* Router transition */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .mobile-header {
    display: flex;
  }

  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    z-index: 100;
    height: 100vh;
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .sidebar.mobile-hidden {
    transform: translateX(-100%);
  }

  .sidebar.mobile-open {
    transform: translateX(0);
  }

  .main-content {
    padding: 68px 12px 12px;
  }
}

@media (max-width: 480px) {
  .main-content {
    padding: 60px 8px 8px;
  }
}
</style>
