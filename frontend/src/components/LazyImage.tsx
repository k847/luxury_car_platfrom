// =============================================================
// 段功能：M6 升级 - 懒加载图片组件
// 说明：IntersectionObserver 延迟加载（进入视口才真正设 src），
//       加载中显示 shimmer 占位，加载完成淡入；支持滚动显现（reveal）。
//       仅动 opacity/transform（GPU 友好），尊重 prefers-reduced-motion。
//       直接用 <img>（无包裹层），尺寸由调用方容器控制。
// =============================================================

import { useEffect, useRef, useState } from "react";

interface Props {
  src?: string | null;
  alt?: string;
  className?: string;
  /** 附加滚动显现动画（进入视口上浮淡入） */
  reveal?: boolean;
}

export default function LazyImage({ src, alt = "", className = "", reveal = false }: Props) {
  const imgRef = useRef<HTMLImageElement>(null);
  const [loaded, setLoaded] = useState(false);
  const [inView, setInView] = useState(!reveal); // 未开启 reveal 时直接可见

  // 懒加载 + reveal 共用一个 IO：进入视口后加载图片并触发显现
  useEffect(() => {
    const node = imgRef.current;
    if (!node) return;
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            setInView(true);
            // 进入视口后才真正设置图片 src，实现懒加载
            if (node.dataset.src && !node.src) node.src = node.dataset.src;
            io.unobserve(node);
          }
        });
      },
      { rootMargin: "160px" } // 提前 160px 预加载，滚动更顺滑
    );
    io.observe(node);
    return () => io.disconnect();
  }, []);

  return (
    <img
      ref={imgRef}
      data-src={src || undefined}
      src={undefined}
      alt={alt}
      loading="lazy"
      className={`${reveal ? "reveal" : ""} ${inView ? "visible" : ""} ${loaded ? "loaded" : "lazy-img"} ${className}`}
      onLoad={() => setLoaded(true)}
      style={{ display: "block", width: "100%", height: "100%", objectFit: "cover" }}
    />
  );
}
