from django.core.management.base import BaseCommand
from ccp_vpm.models import Item, VpmSubmodality

class Command(BaseCommand):
    help = "Carga items demo para VPM (Visual Simbólica e Icónica)"

    def handle(self, *args, **opts):
        Item.objects.all().delete()

        demo_sym = [
            (1, ["A","∆","7"], [["A","7","∆"],["A","∆","7"],["7","A","∆"]], 1, {"flash_ms":1800}),
            (2, ["B","Φ","3","∆"], [["B","3","∆","Φ"],["B","Φ","3","∆"],["Φ","B","3","∆"]], 1, {"flash_ms":1600}),
            (3, ["Q","∑","9","∂","Z"], [["Q","∑","9","∂","Z"],["Q","9","∑","∂","Z"],["Z","∑","9","∂","Q"]], 0, {"flash_ms":1500}),
        ]
        for lvl, seq, opts, correct, params in demo_sym:
            Item.objects.create(
                submodality=VpmSubmodality.VIS_S,
                difficulty_level=lvl,
                stimulus={"symbols": seq},
                options=[{"symbols": o} for o in opts],
                correct_index=correct,
                params=params
            )

        demo_img = [
            (1, {"base":"scene_1"}, [{"change":"none"},{"change":"remove-dot"},{"change":"swap-colors"}], 0, {"flash_ms":1800}),
            (2, {"base":"scene_2"}, [{"change":"none"},{"change":"mirror-left"},{"change":"remove-segment"}], 1, {"flash_ms":1600}),
            (3, {"base":"scene_3"}, [{"change":"remove-small-shape"},{"change":"none"},{"change":"rotate-15"}], 1, {"flash_ms":1500}),
        ]
        for lvl, stim, opts, correct, params in demo_img:
            Item.objects.create(
                submodality=VpmSubmodality.VIS_I,
                difficulty_level=lvl,
                stimulus=stim,
                options=opts,
                correct_index=correct,
                params=params
            )

        self.stdout.write(self.style.SUCCESS("Items demo cargados"))
