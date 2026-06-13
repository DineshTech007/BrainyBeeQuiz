import streamlit as st
import streamlit.components.v1 as components

def display_maths_games():
    # Provide an HTML/JS balloon game!
    
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
      body {
        margin: 0;
        padding: 0;
        overflow: hidden;
        background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: white;
      }
      #game-container {
        position: relative;
        width: 100vw;
        height: 80vh;
        overflow: hidden;
      }
      #top-bar {
        position: absolute;
        top: 0;
        width: 100%;
        display: flex;
        justify-content: space-between;
        padding: 15px 30px;
        box-sizing: border-box;
        font-size: 28px;
        font-weight: 800;
        z-index: 10;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
      }
      #question {
        background: rgba(255, 255, 255, 0.2);
        padding: 10px 30px;
        border-radius: 20px;
        border: 2px solid rgba(255,255,255,0.4);
      }
      #score-box {
        color: #FFD700;
      }
      .balloon {
        position: absolute;
        bottom: -150px;
        width: 70px;
        height: 90px;
        border-radius: 50% 50% 50% 50% / 40% 40% 60% 60%;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 30px;
        font-weight: bold;
        color: white;
        cursor: pointer;
        box-shadow: inset -5px -5px 15px rgba(0,0,0,0.3), 2px 5px 10px rgba(0,0,0,0.4);
        animation-name: floatUp;
        animation-timing-function: linear;
        animation-fill-mode: forwards;
      }
      /* Balloon string */
      .balloon::after {
        content: '';
        position: absolute;
        bottom: -25px;
        left: 34px;
        width: 2px;
        height: 25px;
        background: rgba(255,255,255,0.5);
      }
      /* Balloon knot */
      .balloon::before {
        content: '';
        position: absolute;
        bottom: -5px;
        left: 28px;
        border-left: 7px solid transparent;
        border-right: 7px solid transparent;
        border-bottom: 7px solid inherit; /* Doesn't work exactly with border, we'll use same color */
        border-bottom-color: inherit;
      }
      
      @keyframes floatUp {
        0% { transform: translateY(0) translateX(0) scale(1); }
        33% { transform: translateY(-40vh) translateX(30px) scale(1.05); }
        66% { transform: translateY(-80vh) translateX(-30px) scale(0.95); }
        100% { transform: translateY(-120vh) translateX(0) scale(1); }
      }
      @keyframes pop {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.5); opacity: 0.8; }
        100% { transform: scale(0); opacity: 0; }
      }
      
      .floating-text {
          position: absolute;
          font-size: 40px;
          font-weight: 900;
          pointer-events: none;
          animation: floatFade 1s forwards;
          z-index: 20;
          text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
      }
      @keyframes floatFade {
          0% { opacity: 1; transform: translateY(0) scale(1); }
          100% { opacity: 0; transform: translateY(-80px) scale(1.5); }
      }
      
      .controls {
          position: absolute;
          bottom: 20px;
          width: 100%;
          display: flex;
          justify-content: center;
          gap: 15px;
          z-index: 10;
      }
      .btn {
          background: rgba(255,255,255,0.2);
          border: 2px solid white;
          color: white;
          padding: 10px 20px;
          font-size: 18px;
          font-weight: bold;
          border-radius: 10px;
          cursor: pointer;
          transition: background 0.3s, transform 0.1s;
      }
      .btn:hover { background: rgba(255,255,255,0.4); }
      .btn:active { transform: scale(0.95); }
      .btn.active { background: #FFD700; color: #333; border-color: #FFD700; }
      
      @media (max-width: 600px) {
          #top-bar { font-size: 20px; padding: 10px 15px; }
          .controls { flex-wrap: wrap; gap: 8px; bottom: 10px; }
          .btn { padding: 8px 12px; font-size: 14px; }
          .balloon { width: 50px; height: 65px; font-size: 24px; }
      }
    </style>
    </head>
    <body>
    <div id="game-container">
      <div id="top-bar">
        <div id="question">1 + 1 = ?</div>
        <div id="score-box">⭐ <span id="score">0</span></div>
      </div>
      
      <div class="controls">
          <button class="btn active" id="btn-add" onclick="setOp('+')">Addition</button>
          <button class="btn" id="btn-sub" onclick="setOp('-')">Subtraction</button>
          <button class="btn" id="btn-mul" onclick="setOp('*')">Multiplication</button>
          <button class="btn" id="btn-div" onclick="setOp('/')">Division</button>
      </div>
    </div>
    
    <script>
      let score = 0;
      let currentAnswer = 0;
      let balloons = [];
      let currentOp = '+';
      let spawnInterval;
      const container = document.getElementById('game-container');
      const questionEl = document.getElementById('question');
      const scoreEl = document.getElementById('score');
      const colors = ['#FF5252', '#4CAF50', '#2196F3', '#FFC107', '#9C27B0', '#FF9800', '#00BCD4', '#E91E63'];
    
      function setOp(op) {
          currentOp = op;
          document.querySelectorAll('.btn').forEach(b => b.classList.remove('active'));
          if(op==='+') document.getElementById('btn-add').classList.add('active');
          if(op==='-') document.getElementById('btn-sub').classList.add('active');
          if(op==='*') document.getElementById('btn-mul').classList.add('active');
          if(op==='/') document.getElementById('btn-div').classList.add('active');
          generateQuestion();
      }
    
      function generateQuestion() {
          // clean up old balloons gracefully or immediately
          balloons.forEach(b => b.remove());
          balloons = [];
    
          let a, b;
          if (currentOp === '+') {
              a = Math.floor(Math.random() * 20) + 1;
              b = Math.floor(Math.random() * 20) + 1;
              currentAnswer = a + b;
              questionEl.innerHTML = a + ' + ' + b + ' = ?';
          } else if (currentOp === '-') {
              a = Math.floor(Math.random() * 20) + 10;
              b = Math.floor(Math.random() * a); // ensure positive answer
              currentAnswer = a - b;
              questionEl.innerHTML = a + ' - ' + b + ' = ?';
          } else if (currentOp === '*') {
              a = Math.floor(Math.random() * 12) + 1;
              b = Math.floor(Math.random() * 12) + 1;
              currentAnswer = a * b;
              questionEl.innerHTML = a + ' x ' + b + ' = ?';
          } else if (currentOp === '/') {
              b = Math.floor(Math.random() * 10) + 1;
              currentAnswer = Math.floor(Math.random() * 10) + 1;
              a = b * currentAnswer;
              questionEl.innerHTML = a + ' ÷ ' + b + ' = ?';
          }
    
          spawnBalloonsBatch();
      }
    
      function spawnBalloonsBatch() {
          // Create 1 correct balloon and 4-5 wrong balloons
          let answers = [currentAnswer];
          while(answers.length < 6) {
              let offset = Math.floor(Math.random() * 10) - 5;
              let wrong = currentAnswer + offset;
              if (offset === 0) wrong += 1;
              
              if(wrong >= 0 && !answers.includes(wrong)) {
                  answers.push(wrong);
              }
          }
          
          answers.sort(() => Math.random() - 0.5); // Shuffle
          
          answers.forEach((ans, idx) => {
              createBalloon(ans, idx * 500); // Stagger spawns
          });
      }
    
      function createBalloon(ans, delayMs) {
          setTimeout(() => {
              let balloon = document.createElement('div');
              balloon.className = 'balloon';
              
              let color = colors[Math.floor(Math.random() * colors.length)];
              balloon.style.backgroundColor = color;
              
              // To make border-bottom inherit color for the knot
              balloon.style.borderBottomColor = color;
              
              balloon.style.left = Math.floor(Math.random() * 80) + 10 + '%';
              
              let duration = 6 + Math.random() * 6; // 6 to 12 seconds
              balloon.style.animationDuration = duration + 's';
              balloon.innerHTML = ans;
              
              balloon.onmousedown = function(e) {
                  popBalloon(balloon, ans, e.clientX, e.clientY);
              };
              balloon.ontouchstart = function(e) {
                  popBalloon(balloon, ans, e.touches[0].clientX, e.touches[0].clientY);
              };
              
              container.appendChild(balloon);
              balloons.push(balloon);
              
              // Automatically remove when animation ends to prevent DOM memory leaks
              setTimeout(() => {
                  if (balloon.parentNode) {
                      balloon.remove();
                      // If the correct balloon goes off-screen, we should spawn a new batch!
                      if (ans === currentAnswer) {
                          generateQuestion(); 
                      }
                  }
              }, duration * 1000);
          }, delayMs);
      }
    
      function popBalloon(balloon, ans, x, y) {
          if (balloon.style.animationName === 'pop') return; // already popped
          
          balloon.style.animationName = 'pop';
          balloon.style.animationDuration = '0.3s';
          
          if (ans === currentAnswer) {
              score += 5;
              scoreEl.innerHTML = score;
              showFloatingText(x, y, "+5⭐", "#FFD700");
              setTimeout(() => generateQuestion(), 400); // next question!
          } else {
              if(score > 0) score -= 1; // minor penalty
              scoreEl.innerHTML = score;
              showFloatingText(x, y, "Oops!", "#FF5252");
              setTimeout(() => balloon.remove(), 300);
          }
      }
    
      function showFloatingText(x, y, text, color) {
          let ft = document.createElement('div');
          ft.className = 'floating-text';
          ft.style.left = (x - 20) + 'px';
          ft.style.top = (y - 30) + 'px';
          ft.style.color = color;
          ft.innerHTML = text;
          container.appendChild(ft);
          setTimeout(() => ft.remove(), 1000);
      }
    
      // Start game
      generateQuestion();
    </script>
    </body>
    </html>
    """
    
    components.html(html_code, height=650)
