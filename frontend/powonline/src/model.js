var UserListModel = function () {
  this.data = [
    "John",
    "Jane"
  ];
};

UserListModel.prototype.all = function () {
  return this.data;
};
