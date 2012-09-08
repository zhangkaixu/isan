from isan.common.searcher import Searcher
import isan.tagging.cwssearcher as dfabeam
#import isan.common.dfabeam as dfabeam



class CWSSearcher(Searcher):
    searcher=dfabeam
    raw_to_steps=lambda self,x:len(x)+1
    def __init__(self,schema,beam_width):
        print("welcome")
        self.handler=self.searcher.new(
                beam_width,
                schema.init_stat,
                schema.gen_actions_and_stats,
                schema.gen_features,
                )
