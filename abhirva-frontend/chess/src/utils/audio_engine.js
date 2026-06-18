// Text-To-Speech (TTS) Engine Synchronization
// Target Indian regional accents hi-IN or en-IN as speech fallbacks

class AudioEngine {
  constructor() {
    this.synth = typeof window !== 'undefined' ? window.speechSynthesis : null;
    this.voices = [];
    
    if (this.synth) {
      // Fetch voices asynchronously
      const loadVoices = () => {
        this.voices = this.synth.getVoices();
      };
      loadVoices();
      if (this.synth.onvoiceschanged !== undefined) {
        this.synth.onvoiceschanged = loadVoices;
      }
    }
  }

  getIndianVoice() {
    if (!this.voices || this.voices.length === 0) return null;
    
    // Prioritize high-quality Google voices if available
    let preferredVoice = this.voices.find(voice => voice.lang === 'mr-IN' && voice.name.includes('Google'));
    if (!preferredVoice) {
      preferredVoice = this.voices.find(voice => voice.lang === 'mr-IN');
    }
    if (!preferredVoice) {
      preferredVoice = this.voices.find(voice => voice.lang === 'hi-IN' && voice.name.includes('Google'));
    }
    if (!preferredVoice) {
      preferredVoice = this.voices.find(voice => voice.lang === 'hi-IN');
    }
    
    // Fallback to any English voice
    if (!preferredVoice) {
      preferredVoice = this.voices.find(voice => voice.lang.startsWith('en'));
    }
    
    return preferredVoice || this.voices[0];
  }

  speak(text, speed = 1) {
    if (!this.synth || !text) return;

    // Cancel any ongoing speech
    this.synth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    
    const voice = this.getIndianVoice();
    if (voice) {
      utterance.voice = voice;
    }

    utterance.rate = speed;
    utterance.pitch = 0.95; // Slightly lower pitch for smoother, less robotic voice
    if (voice && voice.lang) {
      utterance.lang = voice.lang;
    }
    
    this.synth.speak(utterance);
  }

  stop() {
    if (this.synth) {
      this.synth.cancel();
    }
  }
}

// Export a singleton instance
const audioEngine = new AudioEngine();
export default audioEngine;
