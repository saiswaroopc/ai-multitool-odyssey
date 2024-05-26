import io


class DataManager:
    def __init__(self, df):
        self.df = df

    def get_dataframe(self):
        return self.df

    def get_dataframe_info(self):
        buffer = io.StringIO()
        self.df.info(buf=buffer)
        return buffer.getvalue()

    def get_dataframe_head(self, n=3):
        return self.df.head(n).to_string()
