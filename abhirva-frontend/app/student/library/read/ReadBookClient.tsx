"use client";
import React, { useEffect, useState, useRef } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Document, Page, pdfjs } from 'react-pdf';
// @ts-ignore
import HTMLFlipBook from 'react-pageflip';

import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import styles from "./read.module.css";

// Configure PDF worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

// Create FlipPage component with forwardRef as required by react-pageflip
const FlipPage = React.forwardRef<HTMLDivElement, any>((props, ref) => {
  return (
    <div ref={ref} className={styles.flipPage} data-density={props.density || "soft"}>
      <Page 
        pageNumber={props.pageNumber} 
        width={props.width} 
        renderTextLayer={false} 
        renderAnnotationLayer={false} 
        className={styles.pdfPage}
      />
      <div className={styles.pageGradient}></div>
    </div>
  );
});
FlipPage.displayName = 'FlipPage';

// For Cover/BackCover if needed
const BookCover = React.forwardRef<HTMLDivElement, any>((props, ref) => {
  return (
    <div ref={ref} className={styles.bookCover} data-density="hard">
      <div className={styles.bookCoverInner}>
        {props.children}
      </div>
    </div>
  );
});
BookCover.displayName = 'BookCover';

export default function ReadBook() {
  const searchParams = useSearchParams();
  const router = useRouter();
  
  const grade = searchParams.get("grade");
  const language = searchParams.get("language") || "English";
  const book = searchParams.get("book");
  
  const [generating, setGenerating] = useState(false);
  const [numPages, setNumPages] = useState<number | null>(null);
  const [windowWidth, setWindowWidth] = useState(800);
  const [isClient, setIsClient] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    setIsClient(true);
    audioRef.current = new Audio("/page-flip.wav");
    
    // Basic anti-copy / anti-right-click
    const handleContextMenu = (e: MouseEvent) => e.preventDefault();
    document.addEventListener("contextmenu", handleContextMenu);
    
    // Track window width for flipbook sizing
    setWindowWidth(window.innerWidth);
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    
    const handleFullscreenChange = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    
    return () => {
      document.removeEventListener("contextmenu", handleContextMenu);
      window.removeEventListener('resize', handleResize);
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  if (!grade || !book) {
    return <div style={{padding: "2rem"}}>Invalid book parameters. <Link href="/student/library">Go Back</Link></div>;
  }

  // Fetch the raw PDF from the API
  const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";
  const pdfUrl = `${BACKEND_URL}/api/library/read?grade=${encodeURIComponent(grade)}&language=${encodeURIComponent(language)}&book=${encodeURIComponent(book)}`;

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages);
  }

  const handleTakeQuiz = () => {
    router.push(`/student/quiz?board=Library&grade=${encodeURIComponent(grade!)}&subject=${encodeURIComponent("Library Book")}&chapter=${encodeURIComponent(book!)}`);
  };

  const toggleFullScreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch((err) => {
        console.error(`Error attempting to enable fullscreen: ${err.message}`);
      });
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  };

  const onFlip = () => {
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
      audioRef.current.play().catch(e => console.log("Audio play failed:", e));
    }
  };

  // Calculate dynamic dimensions for Flipbook based on screen size
  // Ensure it scales up significantly when in fullscreen mode or larger screens
  let bookWidth;
  if (typeof window !== 'undefined') {
      if (windowWidth < 768) {
          bookWidth = windowWidth - 20; // Mobile (single page)
      } else {
          // Desktop (double page spread)
          // Calculate max width based on available height to prevent vertical scrolling
          const availableHeight = isFullscreen ? window.innerHeight - 20 : window.innerHeight - 100;
          const widthFromHeight = availableHeight / 1.3;
          
          // Calculate max width based on available window width
          const availableWidthPerPage = (windowWidth - 60) / 2;
          
          // Use the smaller of the two to ensure it fits perfectly on screen
          bookWidth = Math.min(widthFromHeight, availableWidthPerPage);
      }
  } else {
      bookWidth = 650;
  }
  const bookHeight = bookWidth * 1.3;

  return (
    <div className={styles.readContainer}>
      <div className={styles.realisticBackground}></div>
      <header className={`${styles.header} ${isFullscreen ? styles.hidden : ""}`}>
        <h1 className={styles.title}>{book.replace(".pdf", "")}</h1>
        <div className={styles.actions}>
          <button className={styles.backBtn} onClick={toggleFullScreen}>
            {isFullscreen ? "⛶ Exit Full Screen" : "⛶ Full Screen"}
          </button>
          <Link href="/student/library" className={styles.backBtn}>
            Close Book
          </Link>
          <button 
            className={styles.quizBtn} 
            onClick={handleTakeQuiz}
          >
            Take Book Quiz
          </button>
        </div>
      </header>

      {isFullscreen && (
        <div className={styles.floatingControls}>
          <button 
            className={styles.backBtn} 
            onClick={toggleFullScreen}
            style={{ background: 'rgba(0,0,0,0.6)', border: '1px solid rgba(255,255,255,0.3)' }}
          >
            ⛶ Exit Full Screen
          </button>
          <button 
            className={styles.quizBtn} 
            onClick={handleTakeQuiz}
          >
            Take Book Quiz
          </button>
        </div>
      )}

      <div className={styles.bookWrapper}>
        {isClient && (
          <Document 
            file={pdfUrl} 
            onLoadSuccess={onDocumentLoadSuccess} 
            loading={<div className={styles.loadingBook}>Opening your book...</div>}
            error={<div className={styles.loadingBook}>Failed to load book.</div>}
          >
            {numPages && (
              // @ts-ignore - react-pageflip types are incomplete
              <HTMLFlipBook 
                width={bookWidth} 
                height={bookHeight} 
                size="stretch"
                minWidth={315}
                maxWidth={2000}
                minHeight={400}
                maxHeight={2500}
                showCover={true}
                mobileScrollSupport={true}
                className={styles.flipBook}
                style={{ margin: '0 auto', overflow: 'visible' }}
                usePortrait={windowWidth < 768} // Single page view on mobile
                onFlip={onFlip}
              >
                {/* Cover */}
                <BookCover>
                  <h2>{book.replace(".pdf", "")}</h2>
                  <p>{grade} • {language}</p>
                  <div className={styles.coverInstruction}>Swipe or Click to open</div>
                </BookCover>

                {/* PDF Pages */}
                {Array.from(new Array(numPages), (el, index) => (
                  <FlipPage 
                    key={`page_${index + 1}`} 
                    pageNumber={index + 1} 
                    width={bookWidth} 
                  />
                ))}

                {/* Back Cover */}
                <BookCover>
                  <h2>The End</h2>
                  <button className={styles.backCoverQuizBtn} onClick={handleTakeQuiz}>
                      Take Quiz Now!
                  </button>
                </BookCover>

              </HTMLFlipBook>
            )}
          </Document>
        )}
      </div>
    </div>
  );
}
