/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 基础色板 - 白色主题
        'base': {
          'bg': '#ffffff',        // 白色背景
          'paper': '#ffffff',     // 纸张/面板背景
          'card': '#ffffff',      // 卡片背景
          'elevated': '#f5f5f5',  // 悬浮卡片
        },
        // 品牌色 - 蓝色主调
        'brand': {
          'primary': '#102375',   // 深蓝色 - 主色调
          'secondary': '#4e66cc', // 蓝色 - 次要色
          'muted': '#666666',     // 柔和灰色文字
          'deep': '#102375',      // 深蓝色（保留兼容）
          'sky': '#73a2f3',       // 浅蓝色（兼容旧代码）
          'cyan': '#6fbcce',      // 青色（兼容）
          'light': '#000000',     // 黑色（原浅蓝色看不清）
        },
        // 强调色
        'accent': {
          'danger': '#102375',    // 深蓝色
          'warning': '#4e66cc',   // 蓝色
          'caution': '#73a2f3',   // 浅蓝色
          'success': '#6fbcce',   // 青色
          'info': '#73a2f3',      // 浅蓝色
        },
        // 文字颜色
        'text': {
          'primary': '#000000',   // 黑色主要文字
          'secondary': '#666666', // 灰色次要文字
          'muted': '#999999',     // 更淡的灰色文字
        }
      },
      fontFamily: {
        'sans': ['ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', 'Helvetica', 'Arial', 'sans-serif'],
        'mono': ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace'],
      },
      backgroundImage: {
        'gradient-brand': 'linear-gradient(180deg, #ffffff, #f5f5f5)',
        'gradient-radial-tl': 'radial-gradient(1100px 520px at 18% 0%, rgba(16,35,117,0.05), transparent 60%)',
        'gradient-radial-tr': 'radial-gradient(900px 520px at 82% 10%, rgba(78,102,204,0.05), transparent 55%)',
        'gradient-card': 'linear-gradient(135deg, rgba(16,35,117,0.03) 0%, rgba(115,162,243,0.03) 100%)',
      },
      borderColor: {
        'line': 'rgba(0,0,0,0.12)',
        'line-light': 'rgba(0,0,0,0.08)',
      },
      backdropBlur: {
        'glass': '10px',
      },
      boxShadow: {
        'card': '0 2px 8px rgba(0,0,0,0.1)',
        'glow-brand': '0 4px 12px rgba(16,35,117,0.15)',
        'glow-danger': '0 4px 12px rgba(16,35,117,0.15)',
        'glow-success': '0 4px 12px rgba(111,188,206,0.15)',
      },
      borderRadius: {
        'card': '16px',
        'card-sm': '12px',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'pulse-slow': 'pulse 3s infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(16,35,117,0.2)' },
          '100%': { boxShadow: '0 0 20px rgba(16,35,117,0.4)' },
        },
      },
    },
  },
  plugins: [],
}

