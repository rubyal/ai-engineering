"""Orquestador concurrente de modelos (simulado) - Python 3.12+

Escenarios:
  1. asyncio.gather con 3 modelos dentro del timeout (todo OK).
  2. asyncio.gather con un modelo lento -> TimeoutError capturado.
  3. 10 llamadas con Semaphore(2): máximo 2 en ejecución simultánea.
"""

import asyncio
import sys
import time

assert sys.version_info >= (3, 12), "Se requiere Python 3.12+"

TIMEOUT_SEGUNDOS = 2
MAX_CONCURRENTES = 2

T0 = time.perf_counter()


def log(msg: str) -> None:
    """Log con tiempo relativo desde el inicio del programa."""
    print(f"[{time.perf_counter() - T0:5.2f}s] {msg}")


# ---------------------------------------------------------------------------
# 2. Simulación de llamadas (latencia no bloqueante con asyncio.sleep)
# ---------------------------------------------------------------------------
async def gpt_4_call(prompt: str, latencia: float = 1.2) -> str:
    log("gpt_4_call      -> INICIA")
    await asyncio.sleep(latencia)
    log("gpt_4_call      <- TERMINA")
    return f"[gpt-4] respuesta a '{prompt}'"


async def claude_3_call(prompt: str, latencia: float = 0.8) -> str:
    log("claude_3_call   -> INICIA")
    await asyncio.sleep(latencia)
    log("claude_3_call   <- TERMINA")
    return f"[claude-3] respuesta a '{prompt}'"


async def local_llama_call(prompt: str, latencia: float = 0.5) -> str:
    log("local_llama_call-> INICIA")
    await asyncio.sleep(latencia)
    log("local_llama_call<- TERMINA")
    return f"[llama-local] respuesta a '{prompt}'"


# ---------------------------------------------------------------------------
# 3 + 4. Orquestación con gather y timeout global
# ---------------------------------------------------------------------------
async def orquestar(prompt: str, latencia_llama: float) -> list[str] | None:
    """Dispara los 3 modelos a la vez; timeout total de 2 s."""
    try:
        async with asyncio.timeout(TIMEOUT_SEGUNDOS):
            resultados = await asyncio.gather(
                gpt_4_call(prompt),
                claude_3_call(prompt),
                local_llama_call(prompt, latencia=latencia_llama),
            )
        for r in resultados:
            log(f"RESULTADO: {r}")
        return resultados
    except TimeoutError:
        log(f"ERROR: TimeoutError - la ejecución superó {TIMEOUT_SEGUNDOS}s. "
            "Se cancelaron las llamadas pendientes; el programa continúa.")
        return None


# ---------------------------------------------------------------------------
# 5. Control de flujo con Semaphore
# ---------------------------------------------------------------------------
class Contador:
    """Mide la concurrencia real para validar el Semaphore."""

    def __init__(self) -> None:
        self.activas = 0
        self.maximo = 0


async def llamada_limitada(
    i: int, sem: asyncio.Semaphore, contador: Contador, latencia: float = 0.3
) -> str:
    async with sem:
        contador.activas += 1
        contador.maximo = max(contador.maximo, contador.activas)
        log(f"simulación #{i:02d} -> INICIA  (activas: {contador.activas})")
        await asyncio.sleep(latencia)
        log(f"simulación #{i:02d} <- TERMINA")
        contador.activas -= 1
        return f"resultado #{i:02d}"


async def orquestar_con_semaforo(n: int = 10) -> None:
    sem = asyncio.Semaphore(MAX_CONCURRENTES)
    contador = Contador()
    try:
        async with asyncio.timeout(TIMEOUT_SEGUNDOS):
            resultados = await asyncio.gather(
                *(llamada_limitada(i, sem, contador) for i in range(1, n + 1))
            )
        log(f"{len(resultados)} llamadas completadas. "
            f"Máximo simultáneo observado: {contador.maximo} (límite {MAX_CONCURRENTES})")
    except TimeoutError:
        log("ERROR: TimeoutError en el lote con semáforo.")


# ---------------------------------------------------------------------------
async def main() -> None:
    print("\n=== Escenario 1: 3 modelos en paralelo, dentro del timeout ===")
    await orquestar("hola", latencia_llama=0.5)

    print("\n=== Escenario 2: llama local lento (3 s) -> TimeoutError ===")
    await orquestar("hola", latencia_llama=3.0)

    print(f"\n=== Escenario 3: 10 llamadas, Semaphore({MAX_CONCURRENTES}) ===")
    await orquestar_con_semaforo(10)

    log("Programa finalizado sin detenerse por errores.")


if __name__ == "__main__":
    asyncio.run(main())
