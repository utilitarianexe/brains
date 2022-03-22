import argparse

my_parser = argparse.ArgumentParser(description='Run brains')

my_parser.add_argument('DisplayType',
                       metavar='display',
                       type=str,
                       help='Either pyplot or pygame')


args = my_parser.parse_args()
display_type = args.DisplayType

if display_type == "pygame":
    import display
    display.run_handwriting()
elif display_type == "pyplot":
    import play
    play.run_simple()
else:
    print("must select pyplot or pygame for display option")


