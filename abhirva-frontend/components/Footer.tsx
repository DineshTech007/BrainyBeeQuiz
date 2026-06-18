export default function Footer() {
  return (
    <footer style={{
      padding: '2rem',
      textAlign: 'center',
      borderTop: '1px solid rgba(255, 255, 255, 0.1)',
      backgroundColor: 'rgba(5, 5, 15, 0.8)',
      marginTop: 'auto'
    }}>
      <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
        &copy; {new Date().getFullYear()} Abhirva Learning Solutions. All rights reserved.
      </p>
    </footer>
  );
}
