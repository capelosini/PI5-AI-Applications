export default function GameBoard({ board }) {
    if (!board) return null;

    return (
        <div className="game-board">
            {board.map((row, rowIndex) => (
                <div key={rowIndex} className="board-row">
                    {row.map((cell, colIndex) => (
                        <div 
                            key={`${rowIndex}-${colIndex}`} 
                            className={`board-cell level-${cell.level}`}
                        >
                            {cell.level > 0 && <span className="cell-level">{cell.level}</span>}
                            {cell.professor && (
                                <div className="professor-token">
                                    {cell.professor.substring(0, 1)}
                                    <span className="professor-tooltip">{cell.professor}</span>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            ))}
        </div>
    );
}
