export default function AppLayout({ children = null }) {
    return (
        <>
            <header>
                <h1>AI Applications PI 5</h1>
            </header>
            <main>
                {children}
            </main>
            <footer>
                <p>Base Test</p>
            </footer>
        </>
    )
}