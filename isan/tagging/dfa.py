
import isan.tagging.dfabeam as dfabeam



class DFA:
    def __init__(self,schema,beam_width):
        self.dfa=dfabeam.new(
                beam_width,
                schema.init_stat,
                schema.gen_actions_and_stats,
                schema.gen_features,
                )
        
    def set_action(self,action,d):
        dfabeam.set_action(self.dfa,action,d)
        
    def __del__(self):
        dfabeam.delete(self.dfa)
    
    def update_action(self,stat,action,delta,step):
        dfabeam.update_action(self.dfa,stat,action,delta,step)
    def export_weights(self,step):
        return dfabeam.export_weights(self.dfa,step)

    def set_raw(self,raw):
        dfabeam.set_raw(self.dfa,raw)
    def search(self,step):
        return dfabeam.search(self.dfa,step)

