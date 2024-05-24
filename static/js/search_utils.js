const fetchData = (url) => {

  return fetch(url).then(function (response) {
    if (response.ok) {
      return response.json();
    }
    return response.json().then(function (json) {
      throw json;
    });
  }).then(function (data) {
    //console.log('myFetch', data);
    return Promise.resolve(data);
  }).catch(function (error) {
    console.warn(error);
    throw error;
  });
};

const getE = (id) => { return document.getElementById(id); }
const getEon = (id, func) => { document.getElementById(id).onclick = func; }
const createE = (tag) => { return document.createElement(tag); }

//via: https://vanillajstoolkit.com/helpers/serialize/
/*!
 * Serialize all form data into an object
 * (c) 2021 Chris Ferdinandi, MIT License, https://gomakethings.com
 * @param  {FormData} data The FormData object to serialize
 * @return {String}        The serialized form data
 */
function serialize (data) {
  let obj = {};
  for (let [key, value] of data) {
    if (obj[key] !== undefined) {
      if (!Array.isArray(obj[key])) {
	obj[key] = [obj[key]];
      }
      obj[key].push(value);
    } else {
      obj[key] = value;
    }
  }
  return obj;
}

/**
 * practice javascript class, moogoo
 */
class Paginator {
  constructor(pageIndex, perPage) {
    const DEFAULT_PER_PAGE = 20;
    try {
      if (pageIndex !== null && perPage!== null) {
        pageIndex = parseInt(pageIndex);
        perPage = parseInt(perPage);
        pageIndex = (isNaN(pageIndex)) ? 0 : pageIndex;
        perPage = (isNaN(perPage)) ? DEFAULT_PER_PAGE : perPage;
      } else {
        pageIndex = 0;
        perPage = DEFAULT_PER_PAGE;
      }
    } finally {
      this.pageIndex = pageIndex;
      this.perPage = perPage;
    }
  }

  _int(value) {
    return (isNaN(parseInt(value))) ? 0 : parseInt(value);
  }

  setTotal(value) {
    this.total = this._int(value);
  }

  setPage(value) {
    this.pageIndex = this._int(value);
  }

  setPerPage(value) {
    this.perPage = this._int(value);
    this.pageIndex = 0;
  }

  get hasNext() {
    //let numPage = Math.ceil(this.total/this.perPage);
    if ( this.total > 0
      && (this.pageIndex + 1) * this.perPage < this.total ) {
      return true;
    }
    return false;
  }

  get hasPrevious() {
    if ( this.pageIndex > 0) {
      return true;
    }
    return false;
  }

  get startSequence() {
    return (this.pageIndex * this.perPage) + 1;
  }

  get endSequence() {
    return (this.hasNext) ? (this.pageIndex + 1) * this.perPage : this.total;
  }
}

export { fetchData, getE, getEon, createE, serialize, Paginator };
