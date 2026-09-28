from renderer import Renderer


def main():
    renderer = Renderer()

    print("ZeraWave Renderer Contract Test")
    print("---------------------------------")

    try:
        renderer.initialize()
    except NotImplementedError:
        print("initialize() -> Not implemented")

    try:
        renderer.render({})
    except NotImplementedError:
        print("render()     -> Not implemented")

    try:
        renderer.shutdown()
    except NotImplementedError:
        print("shutdown()   -> Not implemented")

    print()
    print("Renderer contract exists.")


if __name__ == "__main__":
    main()