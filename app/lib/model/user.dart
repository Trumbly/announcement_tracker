import 'package:uuid/uuid.dart';

class User {
  late String _userId;
  late String _email;
  late String _forname;
  late String _surename;
  late String _password;
  User(String email, String forname, String surename, String password,
      {String? userId}) {
    _userId = userId ?? Uuid().v4();
    _email = email;
    _forname = forname;
    _surename = surename;
    _password = password;
  }

  get userId => this._userId;

  get email => this._email;

  set email(value) => this._email = value;

  get forname => this._forname;

  set forname(value) => this._forname = value;

  get surename => this._surename;

  set surename(value) => this._surename = value;

  get hashedPassword => this._password;

  set hashedPassword(value) => this._password = value;
}
