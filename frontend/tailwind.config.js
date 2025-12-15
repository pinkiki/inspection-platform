/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 基础色板 - 深灰色调，更清爽
        'base': {
          'bg': '#0b1220',        // 深色背景
          'paper': '#0f1b2e',     // 纸张/面板背景
          'card': '#111f36',      // 卡片背景
          'elevated': '#162847',  // 悬浮卡片
        },
        // 品牌色 - 青色主调
        'brand': {
          'primary': '#5bd6ff',   // 品牌青 - 主色调
          'secondary': '#4eb8e0', // 次要青
          'muted': '#8aa4c6',     // 柔和文字
          'deep': '#0f1b2e',      // 深色背景（保留兼容）
          'sky': '#5bd6ff',       // 青蓝（兼容旧代码）
          'cyan': '#5bd6ff',      // 青蓝（兼容）
          'light': '#e7f0ff',     // 浅色文字
        },
        // 强调色 - 更鲜艳清晰
        'accent': {
          'danger': '#ff5a7a',    // 柔和红
          'warning': '#ffd166',   // 金黄色
          'caution': '#ffb347',   // 橙色
          'success': '#2ee59d',   // 翠绿色
          'info': '#5bd6ff',      // 信息青
        },
        // 文字颜色
        'text': {
          'primary': '#e7f0ff',   // 主要文字
          'secondary': '#8aa4c6', // 次要文字
          'muted': 'rgba(231,240,255,0.5)', // 更淡的文字
        }
      },
      fontFamily: {
        'sans': ['ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', 'Helvetica', 'Arial', 'sans-serif'],
        'mono': ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace'],
      },
      backgroundImage: {
        'gradient-brand': 'linear-gradient(180deg, #071021, #0b1220)',
        'gradient-radial-tl': 'radial-gradient(1100px 520px at 18% 0%, rgba(91,214,255,0.14), transparent 60%)',
        'gradient-radial-tr': 'radial-gradient(900px 520px at 82% 10%, rgba(255,90,122,0.12), transparent 55%)',
        'gradient-card': 'linear-gradient(135deg, rgba(91,214,255,0.08) 0%, rgba(255,90,122,0.04) 100%)',
      },
      borderColor: {
        'line': 'rgba(255,255,255,0.12)',
        'line-light': 'rgba(255,255,255,0.08)',
      },
      backdropBlur: {
        'glass': '10px',
      },
      boxShadow: {
        'card': '0 14px 30px rgba(0,0,0,0.35)',
        'glow-brand': '0 10px 22px rgba(91,214,255,0.12)',
        'glow-danger': '0 8px 20px rgba(255,90,122,0.15)',
        'glow-success': '0 8px 20px rgba(46,229,157,0.15)',
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
          '0%': { boxShadow: '0 0 5px rgba(91,214,255,0.2)' },
          '100%': { boxShadow: '0 0 20px rgba(91,214,255,0.4)' },
        },
      },
    },
  },
  plugins: [],
}

