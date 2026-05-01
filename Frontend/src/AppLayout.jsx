export default function AppLayout({ children = null }) {
  return (
    <>
      <main>{children}</main>
      <footer>
        <p>HoneyPot Team</p>
      </footer>
    </>
  );
}
