import PropTypes from "prop-types";
import React from "react";
import { graphql } from "gatsby";
import "core-js/fn/array/find";

import { FaTag } from "react-icons/fa/";
import Article from "../components/Article";
import Search from "../components/Search";
import { ThemeContext } from "../layouts";
import Seo from "../components/Seo";
import List from "../components/List";

import AlgoliaIcon from "!svg-react-loader!../images/svg-icons/search-by-algolia.svg?name=AlgoliaLogo";

const WorksPage = props => {
  const {
    data: {
      posts: { edges: posts },
      site: {
        siteMetadata: { facebook, algolia }
      }
    }
  } = props;

  // Create category list
  const categories = {};
  posts.forEach(edge => {
    const {
      node: {
        frontmatter: { category }
      }
    } = edge;

    if (category && category != null) {
      if (!categories[category]) {
        categories[category] = [];
      }
      categories[category].push(edge);
    }
  });

  const categoryList = [];

  for (var key in categories) {
    categoryList.push([key, categories[key]]);
  }

  return (
    <React.Fragment>
      <ThemeContext.Consumer>
        {theme => (
          <div className="wrapper">
            <Article theme={theme} className="article">
              <div className="icon">
                <AlgoliaIcon />
              </div>

              <Search algolia={algolia} theme={theme} />
            </Article>
            <div className="side">
              {categoryList.map(item => (
                <section key={item[0]}>
                  <h2>
                    <FaTag /> {item[0]}
                  </h2>
                  <List edges={item[1]} theme={theme} />
                </section>
              ))}
            </div>
          </div>
        )}
      </ThemeContext.Consumer>

      <Seo facebook={facebook} />

      {/* --- STYLES --- */}
      <style jsx>{`
        .wrapper {
          display: flex;
          flex-wrap: wrap;
        }
        .article {
          flex: 2;
        }
        .side {
          flex: 1;
        }
        .icon {
          display: flex;
          justify-content: flex-end;
          margin-bottom: 20px;
        }
        .icon :global(svg) {
          height: 30px;
        }
      `}</style>
    </React.Fragment>
  );
};

WorksPage.propTypes = {
  data: PropTypes.object.isRequired
};

export default WorksPage;

//eslint-disable-next-line no-undef
export const query = graphql`
  query WorksQuery {
    posts: allMarkdownRemark(
      filter: { fileAbsolutePath: { regex: "//posts/[0-9]+.*--/" } }
      sort: { fields: [fields___prefix], order: DESC }
    ) {
      edges {
        node {
          excerpt
          fields {
            slug
            prefix
          }
          frontmatter {
            title
            category
            author
            cover {
              children {
                ... on ImageSharp {
                  fluid(maxWidth: 800, maxHeight: 360) {
                    ...GatsbyImageSharpFluid_withWebp
                  }
                }
              }
            }
          }
        }
      }
    }
    site {
      siteMetadata {
        facebook {
          appId
        }
        algolia {
          appId
          searchOnlyApiKey
          indexName
        }
      }
    }
  }
`;
