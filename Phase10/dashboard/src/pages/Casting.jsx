import useTranslation from "../hooks/useTranslation";
import PAGE_CONTENT from "../data/pageContent";
import SubPage from "./SubPage";

const c = PAGE_CONTENT.casting;
const PageCasting = ({ onReport }) => {
  const { t } = useTranslation();
  return (
    <SubPage id="casting" title={c.title}
      dataset={c.datasetKeys.map(k => t(k))}
      insights={c.insightKeys.map(k => t(k))}
      models={c.models} columns={c.columns} colLabels={c.colLabels}
      images={c.images} imgBase={c.imgBase} onReport={onReport} />
  );
};

export default PageCasting;
